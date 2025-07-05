"""Conversation management for multi-LLM discussions."""
import asyncio
import time
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from .client import BaseLLMClient, Message, ChatResponse

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states."""
    WAITING = "waiting"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationConfig:
    """Configuration for a conversation."""
    topic: str
    max_rounds: int = 10
    max_participants: int = 4
    round_timeout: float = 60.0  # seconds
    system_prompt: str = field(default="")
    
    def __post_init__(self):
        if not self.system_prompt:
            self.system_prompt = f"""你是一个AI助手，正在参与关于"{self.topic}"的多方讨论。

讨论规则：
1. 请就主题发表你的观点和见解
2. 认真倾听其他参与者的观点
3. 可以提出问题、反驳或补充
4. 保持讨论的建设性和深度
5. 每次回复控制在200字以内
6. 避免重复之前已经充分讨论的内容

当前讨论主题：{self.topic}"""


@dataclass
class ConversationRound:
    """Represents a single round of conversation."""
    round_number: int
    messages: List[Message] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate round duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class Conversation:
    """Represents a complete conversation."""
    id: str
    config: ConversationConfig
    participants: List[str] = field(default_factory=list)
    rounds: List[ConversationRound] = field(default_factory=list)
    state: ConversationState = ConversationState.WAITING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def add_round(self, round_obj: ConversationRound):
        """Add a new round to the conversation."""
        self.rounds.append(round_obj)
        self.updated_at = time.time()
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages from all rounds."""
        messages = []
        for round_obj in self.rounds:
            messages.extend(round_obj.messages)
        return messages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "topic": self.config.topic,
            "participants": self.participants,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "messages": [
                        {
                            "role": m.role,
                            "content": m.content,
                            "platform": m.platform,
                            "timestamp": m.timestamp
                        }
                        for m in r.messages
                    ],
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "duration": r.duration
                }
                for r in self.rounds
            ]
        }


class ConversationManager:
    """Manages multi-LLM conversations."""
    
    def __init__(self, clients: List[BaseLLMClient]):
        # Convert list of clients to dictionary for easier lookup
        self.clients = {client.platform_name: client for client in clients}
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation: Optional[str] = None
    
    def create_conversation(self, config: ConversationConfig, participant_platforms: List[str]) -> str:
        """Create a new conversation."""
        # Validate participants
        available_platforms = set(self.clients.keys())
        requested_platforms = set(participant_platforms)
        
        if not requested_platforms.issubset(available_platforms):
            missing = requested_platforms - available_platforms
            raise ValueError(f"Platforms not available: {missing}")
        
        if len(participant_platforms) > config.max_participants:
            raise ValueError(f"Too many participants: {len(participant_platforms)} > {config.max_participants}")
        
        conversation_id = f"conv_{int(time.time())}_{len(self.conversations)}"
        conversation = Conversation(
            id=conversation_id,
            config=config,
            participants=participant_platforms
        )
        
        self.conversations[conversation_id] = conversation
        logger.info(f"Created conversation {conversation_id} with participants: {participant_platforms}")
        
        return conversation_id
    
    async def start_conversation(self, conversation_id: str, 
                               progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> Conversation:
        """Start a conversation."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation.state = ConversationState.RUNNING
        self.active_conversation = conversation_id
        
        try:
            # Add system message
            system_message = Message(
                role="system",
                content=conversation.config.system_prompt,
                timestamp=time.time()
            )
            
            # Initial context for all participants
            initial_context = [system_message]
            
            for round_num in range(1, conversation.config.max_rounds + 1):
                if conversation.state != ConversationState.RUNNING:
                    break
                
                round_obj = ConversationRound(round_number=round_num, start_time=time.time())
                
                if progress_callback:
                    progress_callback("round_start", {
                        "round": round_num,
                        "total_rounds": conversation.config.max_rounds
                    })
                
                # Each participant responds in this round
                for platform in conversation.participants:
                    if conversation.state != ConversationState.RUNNING:
                        break
                    
                    try:
                        # Get conversation context
                        context = initial_context + conversation.get_all_messages()
                        
                        # Add a prompt for the current participant
                        if round_num == 1:
                            user_prompt = f"请开始讨论话题：{conversation.config.topic}。分享你的初步观点。"
                        else:
                            user_prompt = f"基于以上讨论，请继续就话题'{conversation.config.topic}'发表你的观点。"
                        
                        context.append(Message(
                            role="user",
                            content=user_prompt,
                            timestamp=time.time()
                        ))
                        
                        if progress_callback:
                            progress_callback("participant_thinking", {
                                "platform": platform,
                                "round": round_num
                            })
                        
                        # Get response from LLM
                        client = self.clients[platform]
                        response = await asyncio.wait_for(
                            client.chat(context),
                            timeout=conversation.config.round_timeout
                        )
                        
                        # Create response message
                        message = Message(
                            role="assistant",
                            content=response.content,
                            platform=platform,
                            timestamp=time.time()
                        )
                        
                        round_obj.messages.append(message)
                        
                        if progress_callback:
                            progress_callback("participant_response", {
                                "platform": platform,
                                "round": round_num,
                                "message": message.content
                            })
                        
                        # Small delay between participants
                        await asyncio.sleep(1)
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout for {platform} in round {round_num}")
                        error_msg = Message(
                            role="assistant",
                            content="[响应超时]",
                            platform=platform,
                            timestamp=time.time()
                        )
                        round_obj.messages.append(error_msg)
                    except Exception as e:
                        error_str = str(e)
                        logger.error(f"Error for {platform} in round {round_num}: {e}")
                        
                        # 生成用户友好的错误消息，确保不为空
                        if "404" in error_str and "NotFound" in error_str:
                            if platform == "火山豆包":
                                error_content = "[配置错误: 火山豆包endpoint ID无效，请检查DOUBAO_MODEL配置]"
                            else:
                                error_content = "[模型不存在或无权限访问]"
                        elif "402" in error_str and "Payment Required" in error_str:
                            error_content = "[账户余额不足，请充值]"
                        elif "401" in error_str or "Unauthorized" in error_str:
                            error_content = "[API密钥无效]"
                        elif "429" in error_str:
                            error_content = "[请求频率超限，请稍后重试]"
                        elif "400" in error_str and "empty" in error_str:
                            error_content = "[消息格式错误，可能包含空内容]"
                        else:
                            error_content = f"[错误: {error_str[:100]}...]" if len(error_str) > 100 else f"[错误: {error_str}]"
                        
                        # 确保错误内容不为空
                        if not error_content or error_content.strip() == "":
                            error_content = f"[{platform}发生未知错误]"
                        
                        error_msg = Message(
                            role="assistant",
                            content=error_content,
                            platform=platform,
                            timestamp=time.time()
                        )
                        round_obj.messages.append(error_msg)
                
                round_obj.end_time = time.time()
                conversation.add_round(round_obj)
                
                if progress_callback:
                    progress_callback("round_complete", {
                        "round": round_num,
                        "duration": round_obj.duration
                    })
                
                # Small delay between rounds
                await asyncio.sleep(2)
            
            conversation.state = ConversationState.COMPLETED
            
        except Exception as e:
            logger.error(f"Error in conversation {conversation_id}: {e}")
            conversation.state = ConversationState.ERROR
            raise
        finally:
            if self.active_conversation == conversation_id:
                self.active_conversation = None
        
        return conversation
    
    def pause_conversation(self, conversation_id: str):
        """Pause an active conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation and conversation.state == ConversationState.RUNNING:
            conversation.state = ConversationState.PAUSED
            logger.info(f"Paused conversation {conversation_id}")
    
    def resume_conversation(self, conversation_id: str):
        """Resume a paused conversation."""
        conversation = self.conversations.get(conversation_id)
        if conversation and conversation.state == ConversationState.PAUSED:
            conversation.state = ConversationState.RUNNING
            logger.info(f"Resumed conversation {conversation_id}")
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def list_conversations(self) -> List[Conversation]:
        """List all conversations."""
        return list(self.conversations.values())
    
    def export_conversation(self, conversation_id: str) -> str:
        """Export conversation to JSON."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        return json.dumps(conversation.to_dict(), ensure_ascii=False, indent=2) 
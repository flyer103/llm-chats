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
    max_participants: int = 8  # Increased to support all platforms + future expansion
    round_timeout: float = 60.0  # seconds
    system_prompt: str = field(default="")
    
    def __post_init__(self):
        if not self.system_prompt:
            # Default system prompt for multi-participant discussions
            self.system_prompt = f"""你是一个资深专家，正在参与关于"{self.topic}"的深度学术讨论。

深度讨论要求：
1. **内容深度**: 提供深刻、独到的见解，从理论基础、实践应用、发展趋势等多维度分析
2. **字数要求**: 每次回复控制在1000-2000字，确保内容充实而不冗长
3. **逻辑结构**: 使用清晰的论证逻辑，包含问题分析、解决方案、案例验证等
4. **视觉辅助**: 积极使用表格、流程图、对比图等Markdown格式的图表来增强理解
5. **批判思维**: 对其他参与者的观点进行建设性的质疑、补充或扩展
6. **创新观点**: 提出原创性的见解，避免简单重复已有观点
7. **实践导向**: 结合具体案例、数据、实验结果来支撑观点

技术写作要求：
- 使用Markdown格式创建表格对比不同方案
- 用代码块展示关键算法或配置
- 使用列表和编号来组织复杂信息
- 通过引用块突出重要观点或定义

参考文献要求：
- 每个主要观点提供2-3个权威参考链接
- 包含学术论文、技术文档、行业报告等
- 使用格式：[论文标题](DOI链接) 或 [文档标题](官方链接)
- 链接必须真实有效，来源权威可信

当前讨论主题：{self.topic}

请以专业、深入、有见地的方式参与讨论，每轮发言都要有实质性的贡献和独特的价值。"""
    
    def set_system_prompt_for_participants(self, participant_count: int):
        """Set system prompt based on participant count."""
        if participant_count == 1:
            self.system_prompt = f"""你是一位资深研究员，正在对话题"{self.topic}"进行深度独立分析和研究。

深度分析要求：
1. **全面性分析**: 从理论基础、技术实现、应用场景、发展趋势等多个维度进行综合分析
2. **字数要求**: 每轮分析控制在1000-2000字，确保内容深入且结构完整
3. **逻辑递进**: 每轮都在前一轮基础上深入，形成层层递进的分析体系
4. **数据驱动**: 结合具体数据、案例研究、实验结果来支撑分析结论
5. **批判性思维**: 对现有方案进行客观评估，指出优势、局限性和改进方向
6. **前瞻性洞察**: 预测发展趋势，提出创新性的解决方案或研究方向
7. **系统性思考**: 考虑技术、经济、社会、环境等多重因素的相互影响

技术分析规范：
- 使用表格对比不同技术方案的优缺点
- 绘制流程图展示系统架构或处理流程
- 提供代码示例说明关键实现细节
- 使用图表展示性能对比或趋势分析
- 通过引用块突出核心观点和定义

学术研究标准：
- 每个主要论点提供3-5个权威参考文献
- 引用最新的学术论文、技术报告、行业白皮书
- 参考格式：[论文标题](DOI链接) 或 [报告标题](官方链接)
- 确保引用来源的权威性和时效性

当前分析主题：{self.topic}

请以学者的严谨态度进行深度分析，每轮都要有突破性的见解和实质性的贡献，形成具有学术价值的研究成果。"""
        else:
            # Enhanced multi-participant prompt for deep discussions
            self.system_prompt = f"""你是一个资深专家，正在参与关于"{self.topic}"的深度学术讨论。

深度讨论要求：
1. **内容深度**: 提供深刻、独到的见解，从理论基础、实践应用、发展趋势等多维度分析
2. **字数要求**: 每次回复控制在1000-2000字，确保内容充实而不冗长
3. **逻辑结构**: 使用清晰的论证逻辑，包含问题分析、解决方案、案例验证等
4. **视觉辅助**: 积极使用表格、流程图、对比图等Markdown格式的图表来增强理解
5. **批判思维**: 对其他参与者的观点进行建设性的质疑、补充或扩展
6. **创新观点**: 提出原创性的见解，避免简单重复已有观点
7. **实践导向**: 结合具体案例、数据、实验结果来支撑观点

技术写作要求：
- 使用Markdown格式创建表格对比不同方案
- 用代码块展示关键算法或配置
- 使用列表和编号来组织复杂信息
- 通过引用块突出重要观点或定义

参考文献要求：
- 每个主要观点提供2-3个权威参考链接
- 包含学术论文、技术文档、行业报告等
- 使用格式：[论文标题](DOI链接) 或 [文档标题](官方链接)
- 链接必须真实有效，来源权威可信

当前讨论主题：{self.topic}

请以专业、深入、有见地的方式参与讨论，每轮发言都要有实质性的贡献和独特的价值。"""


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
                            "timestamp": m.timestamp,
                            "references": m.references if m.has_references() else []
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
        
        # Set system prompt based on participant count
        config.set_system_prompt_for_participants(len(participant_platforms))
        
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
                
                # 立即添加轮次对象到对话中，这样UI就能显示正在进行的轮次
                conversation.add_round(round_obj)
                
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
                        if len(conversation.participants) == 1:
                            # Single participant - deep analysis mode
                            if round_num == 1:
                                user_prompt = f"请开始深入分析话题：{conversation.config.topic}。从你认为最重要的角度开始分析。"
                            else:
                                user_prompt = f"基于以上分析，请从新的角度继续深入思考话题'{conversation.config.topic}'。"
                        else:
                            # Multi-participant - discussion mode
                            if round_num == 1:
                                user_prompt = f"请开始讨论话题：{conversation.config.topic}。分享你的初步观点。"
                            else:
                                user_prompt = f"基于以上讨论，请继续就话题'{conversation.config.topic}'发表你的观点。"
                        
                        # Add reference links from previous rounds for validation
                        if round_num > 1:
                            previous_references = self._collect_previous_references(conversation, round_num - 1)
                            if previous_references:
                                reference_text = self._format_references_for_validation(previous_references)
                                user_prompt += f"\n\n以下是其他参与者在之前轮次中提供的参考链接，请在你的回复中验证、引用或补充：\n{reference_text}"
                        
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
                        
                        # Get response from LLM with streaming
                        client = self.clients[platform]
                        
                        # Initialize streaming response
                        streaming_content = ""
                        message_timestamp = time.time()
                        
                        try:
                            stream_successful = False
                            async for chunk in client.stream_chat(context):
                                if conversation.state != ConversationState.RUNNING:
                                    break
                                    
                                streaming_content += chunk
                                stream_successful = True
                                
                                # Send streaming update to UI immediately
                                if progress_callback:
                                    progress_callback("participant_streaming", {
                                        "platform": platform,
                                        "round": round_num,
                                        "partial_content": streaming_content,
                                        "chunk": chunk
                                    })
                                
                                # Minimal delay to prevent overwhelming the UI
                                await asyncio.sleep(0.001)
                                
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"Streaming error for {platform}: {e}")
                            
                            # Classify error type for better handling
                            is_connection_error = any(keyword in error_msg.lower() for keyword in [
                                'connection', 'timeout', 'network', 'unreachable', 'refused'
                            ])
                            
                            is_ollama_error = "ollama" in platform.lower() and is_connection_error
                            
                            # Fall back to non-streaming if streaming fails
                            try:
                                if progress_callback:
                                    progress_callback("participant_thinking", {
                                        "platform": platform,
                                        "round": round_num,
                                        "fallback_reason": "streaming_failed"
                                    })
                                
                                logger.info(f"Attempting fallback to non-streaming for {platform}...")
                                response = await asyncio.wait_for(
                                    client.chat(context),
                                    timeout=conversation.config.round_timeout
                                )
                                streaming_content = response.content
                                logger.info(f"Fallback successful for {platform}")
                                
                            except Exception as fallback_e:
                                fallback_error_msg = str(fallback_e)
                                logger.error(f"Fallback error for {platform}: {fallback_e}")
                                
                                # Generate user-friendly error message based on error type
                                if is_ollama_error:
                                    streaming_content = f"[Ollama连接失败: 请确保Ollama服务正在运行 (ollama serve)]"
                                elif "401" in fallback_error_msg or "unauthorized" in fallback_error_msg.lower():
                                    streaming_content = f"[{platform}认证失败: API密钥无效或已过期]"
                                elif "429" in fallback_error_msg or "rate limit" in fallback_error_msg.lower():
                                    streaming_content = f"[{platform}请求频率超限: 请稍后重试]"
                                elif "timeout" in fallback_error_msg.lower():
                                    streaming_content = f"[{platform}连接超时: 请检查网络连接]"
                                elif "404" in fallback_error_msg:
                                    streaming_content = f"[{platform}模型不存在: 请检查模型配置]"
                                else:
                                    # Truncate very long error messages
                                    error_preview = fallback_error_msg[:100] + "..." if len(fallback_error_msg) > 100 else fallback_error_msg
                                    streaming_content = f"[{platform}服务错误: {error_preview}]"
                        
                        # Create final response message
                        message = Message(
                            role="assistant",
                            content=streaming_content,
                            platform=platform,
                            timestamp=message_timestamp
                        )
                        
                        # Extract references from the response
                        references = message.extract_references_from_content()
                        if references:
                            message.references = references
                            logger.info(f"Extracted {len(references)} references from {platform} response")
                        
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
                        timeout_duration = conversation.config.round_timeout
                        logger.warning(f"Timeout for {platform} in round {round_num} after {timeout_duration}s")
                        
                        if progress_callback:
                            progress_callback("participant_timeout", {
                                "platform": platform,
                                "round": round_num,
                                "timeout_duration": timeout_duration
                            })
                        
                        error_msg = Message(
                            role="assistant",
                            content=f"[响应超时: {platform}在{timeout_duration}秒内未响应，请检查网络连接或增加超时时间]",
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
                # 轮次对象已经在开始时添加到对话中了，这里只需要更新时间
                conversation.updated_at = time.time()
                
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
    
    def get_available_summarizers(self) -> List[str]:
        """Get list of available models for summarization."""
        return list(self.clients.keys())
    
    def can_summarize_conversation(self, conversation_id: str) -> bool:
        """Check if a conversation can be summarized."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        # Can summarize if conversation is completed and has messages
        return (conversation.state == ConversationState.COMPLETED and 
                len(conversation.get_all_messages()) > 0)
    
    def get_summary_statistics(self, conversation_id: str) -> Dict[str, Any]:
        """Get statistics about a conversation for summarization."""
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        messages = conversation.get_all_messages()
        user_assistant_messages = [msg for msg in messages if msg.role in ["user", "assistant"]]
        
        stats = {
            "total_messages": len(messages),
            "content_messages": len(user_assistant_messages),
            "total_rounds": len(conversation.rounds),
            "participants": len(conversation.participants),
            "participant_names": conversation.participants,
            "total_words": sum(len(msg.content.split()) for msg in user_assistant_messages),
            "average_words_per_message": 0,
            "conversation_duration": 0
        }
        
        if user_assistant_messages:
            stats["average_words_per_message"] = stats["total_words"] / len(user_assistant_messages)
        
        # Calculate conversation duration
        if conversation.rounds:
            first_round = conversation.rounds[0]
            last_round = conversation.rounds[-1]
            if first_round.start_time and last_round.end_time:
                stats["conversation_duration"] = last_round.end_time - first_round.start_time
        
        return stats
    
    def _collect_previous_references(self, conversation: Conversation, up_to_round: int) -> List[Dict[str, Any]]:
        """Collect reference links from previous rounds."""
        references = []
        
        for round_obj in conversation.rounds[:up_to_round]:
            for message in round_obj.messages:
                if message.role == "assistant" and message.has_references():
                    for ref in message.references or []:
                        references.append({
                            "platform": message.platform,
                            "round": round_obj.round_number,
                            "title": ref.get("title", ""),
                            "url": ref.get("url", ""),
                            "description": ref.get("description", "")
                        })
        
        return references
    
    def _format_references_for_validation(self, references: List[Dict[str, Any]]) -> str:
        """Format reference links for validation prompt."""
        if not references:
            return ""
        
        formatted_refs = []
        for ref in references:
            platform = ref.get("platform", "未知平台")
            round_num = ref.get("round", 0)
            title = ref.get("title", "未知标题")
            url = ref.get("url", "#")
            description = ref.get("description", "")
            
            if description:
                formatted_refs.append(f"- {platform} (第{round_num}轮): [{title}]({url}) - {description}")
            else:
                formatted_refs.append(f"- {platform} (第{round_num}轮): [{title}]({url})")
        
        return "\n".join(formatted_refs) 
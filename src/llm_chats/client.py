"""LLM client implementations for different platforms."""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, cast
from dataclasses import dataclass
import logging

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import LLMConfig

logger = logging.getLogger(__name__)


def validate_and_clean_messages(messages: List['Message']) -> List['Message']:
    """
    Validate and clean messages to ensure they meet API requirements.
    
    Args:
        messages: List of Message objects to validate
        
    Returns:
        List of cleaned Message objects
    """
    cleaned_messages = []
    
    for msg in messages:
        # Skip assistant messages with empty content
        if msg.role == "assistant" and (not msg.content or msg.content.strip() == ""):
            logger.warning(f"Skipping empty assistant message from {msg.platform}")
            continue
        
        # Ensure content is not None and has some content
        content = msg.content.strip() if msg.content else ""
        
        # Provide default content for empty messages
        if not content:
            if msg.role == "system":
                content = "你是一个AI助手。"
            elif msg.role == "user":
                content = "请继续对话。"
            else:
                content = "[消息内容为空]"
        
        # Create a new message with cleaned content
        cleaned_msg = Message(
            role=msg.role,
            content=content,
            platform=msg.platform,
            timestamp=msg.timestamp
        )
        cleaned_messages.append(cleaned_msg)
    
    return cleaned_messages


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # "system", "user", "assistant"
    content: str
    platform: Optional[str] = None
    timestamp: Optional[float] = None


@dataclass
class ChatResponse:
    """Response from LLM chat completion."""
    content: str
    platform: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.platform_name = config.name
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat(self, messages: List[Message]) -> ChatResponse:
        """Send chat completion request."""
        try:
            # Validate and clean messages
            cleaned_messages = validate_and_clean_messages(messages)
            
            # Ensure we have at least one message
            if not cleaned_messages:
                raise ValueError("No valid messages to send")
            
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in cleaned_messages
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=cast(Any, openai_messages),  # Type cast to handle OpenAI types
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            # Ensure response content is not empty
            response_content = response.choices[0].message.content
            if not response_content or response_content.strip() == "":
                response_content = f"[{self.platform_name}响应内容为空]"
                logger.warning(f"{self.platform_name} returned empty response, using placeholder")
            
            return ChatResponse(
                content=response_content,
                platform=self.platform_name,
                model=self.config.model,
                usage=response.usage.model_dump() if response.usage else None
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # 提供更友好的错误信息
            if "404" in error_msg and "NotFound" in error_msg:
                if self.platform_name == "火山豆包":
                    friendly_msg = f"火山豆包模型配置错误：模型'{self.config.model}'不存在。请检查是否使用了正确的endpoint ID。"
                else:
                    friendly_msg = f"{self.platform_name}模型'{self.config.model}'不存在或无访问权限。"
            elif "402" in error_msg and "Payment Required" in error_msg:
                friendly_msg = f"{self.platform_name}账户余额不足，请充值后重试。"
            elif "401" in error_msg or "Unauthorized" in error_msg:
                friendly_msg = f"{self.platform_name}API密钥无效或已过期。"
            elif "403" in error_msg or "Forbidden" in error_msg:
                friendly_msg = f"{self.platform_name}访问被拒绝，请检查API权限设置。"
            elif "429" in error_msg or "Rate limit" in error_msg.lower():
                friendly_msg = f"{self.platform_name}请求频率超限，请稍后重试。"
            else:
                friendly_msg = f"{self.platform_name}请求失败：{error_msg}"
            
            logger.error(f"Error in {self.platform_name} chat: {friendly_msg}")
            
            # 抛出带有友好信息的异常
            from openai import APIError
            if isinstance(e, APIError):
                e.message = friendly_msg
            raise
    
    async def stream_chat(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """Stream chat completion response."""
        try:
            # Validate and clean messages
            cleaned_messages = validate_and_clean_messages(messages)
            
            # Ensure we have at least one message
            if not cleaned_messages:
                raise ValueError("No valid messages to send")
            
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in cleaned_messages
            ]
            
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=cast(Any, openai_messages),  # Type cast to handle OpenAI types
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in {self.platform_name} stream chat: {e}")
            raise


class AlibabaClient(BaseLLMClient):
    """阿里云百炼 (Alibaba Cloud Model Studio) client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)


class DoubaoClient(BaseLLMClient):
    """火山豆包 (Volcano Engine Doubao) client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)


class MoonshotClient(BaseLLMClient):
    """月之暗面 (Moonshot) client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)


class DeepSeekClient(BaseLLMClient):
    """DeepSeek client."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """Create a client based on the config name."""
        platform_name = config.name.lower()
        
        if "阿里云百炼" in config.name or "alibaba" in platform_name:
            return AlibabaClient(config)
        elif "火山豆包" in config.name or "doubao" in platform_name:
            return DoubaoClient(config)
        elif "月之暗面" in config.name or "moonshot" in platform_name:
            return MoonshotClient(config)
        elif "deepseek" in config.name or platform_name == "deepseek":
            return DeepSeekClient(config)
        else:
            raise ValueError(f"Unsupported platform: {config.name}")
    
    @staticmethod
    def create_all_clients(platform_configs) -> List[BaseLLMClient]:
        """Create clients for all enabled platforms."""
        from .config import PlatformConfigs
        
        clients = []
        for config in platform_configs.get_enabled_configs():
            try:
                client = LLMClientFactory.create_client(config)
                clients.append(client)
                logger.info(f"Created client for {config.name}")
            except Exception as e:
                logger.error(f"Failed to create client for {config.name}: {e}")
        
        if not clients:
            raise ValueError("No valid LLM clients could be created. Please check your configuration.")
        
        return clients 
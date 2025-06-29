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
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=cast(Any, openai_messages),  # Type cast to handle OpenAI types
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            return ChatResponse(
                content=response.choices[0].message.content or "",
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
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
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
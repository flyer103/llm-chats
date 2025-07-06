"""LLM client implementations for different platforms."""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, cast
from dataclasses import dataclass
import logging
import requests

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
    # File attachment support
    attachments: Optional[List[Dict[str, Any]]] = None
    
    def has_attachments(self) -> bool:
        """Check if message has attachments."""
        return self.attachments is not None and len(self.attachments) > 0
    
    def get_attachment_summary(self) -> str:
        """Get a summary of attachments for display."""
        if not self.has_attachments():
            return ""
        
        summaries = []
        # mypy: self.attachments is not None here because has_attachments() returned True
        for attachment in self.attachments or []:
            file_info = attachment.get('file_info', {})
            name = file_info.get('name', 'unknown')
            mime_type = file_info.get('mime_type', 'unknown')
            size = file_info.get('size', 0)
            status = attachment.get('processing_status', 'unknown')
            
            if status == 'success':
                word_count = attachment.get('word_count', 0)
                summaries.append(f"📎 {name} ({mime_type}, {size} bytes, {word_count} words)")
            else:
                summaries.append(f"❌ {name} ({mime_type}, processing failed)")
        
        return "\n".join(summaries)


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
        """Stream chat completion response with robust error handling."""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
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
                
                # If we reach here, streaming was successful
                return
                        
            except Exception as e:
                error_msg = str(e).lower()
                
                # Classify error types
                is_connection_error = any(keyword in error_msg for keyword in [
                    'connection', 'timeout', 'network', 'unreachable', 'refused', 'reset'
                ])
                
                is_rate_limit = any(keyword in error_msg for keyword in [
                    'rate limit', '429', 'too many requests'
                ])
                
                is_auth_error = any(keyword in error_msg for keyword in [
                    '401', '403', 'unauthorized', 'forbidden', 'invalid api key'
                ])
                
                is_server_error = any(keyword in error_msg for keyword in [
                    '500', '502', '503', '504', 'internal server error', 'bad gateway', 
                    'service unavailable', 'gateway timeout'
                ])
                
                # Determine if we should retry
                should_retry = (
                    attempt < max_retries - 1 and 
                    (is_connection_error or is_rate_limit or is_server_error) and
                    not is_auth_error  # Don't retry auth errors
                )
                
                if should_retry:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    if is_rate_limit:
                        delay = max(delay, 5.0)  # Longer delay for rate limits
                    
                    logger.warning(f"{self.platform_name} stream chat attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final attempt or non-retryable error
                    self._log_stream_error(e, attempt + 1)
                    raise self._create_enhanced_exception(e)
    
    def _log_stream_error(self, error: Exception, attempts: int):
        """Log detailed stream error information."""
        error_msg = str(error)
        
        if "ollama" in self.platform_name.lower():
            if any(keyword in error_msg.lower() for keyword in ['connection', 'refused', 'unreachable']):
                logger.error(f"{self.platform_name} stream chat failed after {attempts} attempts: {error}")
                logger.error("💡 Ollama troubleshooting:")
                logger.error("   1. 确保 Ollama 服务正在运行: ollama serve")
                logger.error("   2. 检查端口是否被占用: lsof -i :11434")
                logger.error("   3. 验证模型是否已下载: ollama list")
                logger.error(f"   4. 测试连接: curl http://localhost:11434/api/tags")
            else:
                logger.error(f"{self.platform_name} stream chat failed: {error}")
        else:
            logger.error(f"{self.platform_name} stream chat failed after {attempts} attempts: {error}")
    
    def _create_enhanced_exception(self, original_error: Exception) -> Exception:
        """Create an enhanced exception with better error messages."""
        error_msg = str(original_error)
        
        # Enhanced error messages based on platform and error type
        if "ollama" in self.platform_name.lower():
            if any(keyword in error_msg.lower() for keyword in ['connection', 'refused', 'unreachable']):
                enhanced_msg = f"Ollama 连接失败: {error_msg}\n建议: 请确保 Ollama 服务正在运行 (ollama serve)"
            else:
                enhanced_msg = f"Ollama 服务错误: {error_msg}"
        else:
            # Handle other platforms
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                enhanced_msg = f"{self.platform_name} API密钥无效或已过期: {error_msg}"
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                enhanced_msg = f"{self.platform_name} 请求频率超限: {error_msg}"
            elif "timeout" in error_msg.lower():
                enhanced_msg = f"{self.platform_name} 连接超时: {error_msg}"
            else:
                enhanced_msg = f"{self.platform_name} 流式聊天失败: {error_msg}"
        
        # Create new exception with enhanced message - handle OpenAI SDK compatibility
        try:
            if isinstance(original_error, ConnectionError):
                return ConnectionError(enhanced_msg)
            elif isinstance(original_error, TimeoutError):
                return TimeoutError(enhanced_msg)
            else:
                # Try to create the same exception type
                return type(original_error)(enhanced_msg)
        except TypeError:
            # Fallback for OpenAI SDK exceptions that have different constructors
            logger.warning(f"Could not create enhanced exception of type {type(original_error)}. Using generic ConnectionError.")
            return ConnectionError(enhanced_msg)


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


class OllamaClient(BaseLLMClient):
    """Ollama local model client with enhanced compatibility."""
    
    def __init__(self, config: LLMConfig):
        # First check if Ollama service is accessible
        self._validate_ollama_connection(config.base_url, config.model)
        super().__init__(config)
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3
        
        # Configure client for Ollama compatibility
        self.client.timeout = 30.0  # Increase timeout for local models
    
    async def chat(self, messages: List[Message]) -> ChatResponse:
        """Override chat method to use Ollama native API for non-streaming."""
        try:
            # Use Ollama native API
            content = ""
            async for chunk in self._stream_chat_native(messages):
                content += chunk
            
            # Process content to extract actual response (filter out <think> tags)
            processed_content = self._extract_actual_response(content)
            
            # Ensure response content is not empty
            if not processed_content or processed_content.strip() == "":
                processed_content = f"[{self.platform_name}响应内容为空]"
                logger.warning(f"{self.platform_name} returned empty response, using placeholder")
            
            return ChatResponse(
                content=processed_content,
                platform=self.platform_name,
                model=self.config.model,
                usage=None  # Ollama doesn't provide usage info in native API
            )
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            # Re-raise with enhanced error message
            raise ConnectionError(f"Ollama chat failed: {str(e)}")
    
    def _extract_actual_response(self, content: str) -> str:
        """
        Extract the actual response from Ollama content, filtering out <think> tags.
        
        Args:
            content: Raw content from Ollama that may contain <think>...</think> tags
            
        Returns:
            Cleaned content with actual response only
        """
        import re
        
        # Check if content contains <think> tags
        if '<think>' in content and '</think>' in content:
            # Remove all content between <think> and </think> tags
            cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            # Clean up extra whitespace
            cleaned_content = cleaned_content.strip()
            
            # If we have cleaned content, return it
            if cleaned_content:
                logger.debug(f"Filtered out think tags. Original length: {len(content)}, Cleaned length: {len(cleaned_content)}")
                return cleaned_content
            else:
                logger.warning("After filtering think tags, no content remained!")
                return content  # Return original if cleaning left nothing
        
        # No think tags found, return original content
        return content
    
    def _validate_ollama_connection(self, base_url: str, model_name: str):
        """Validate that Ollama service is running and accessible."""
        # Extract the base URL without the /v1 suffix for health check
        health_url = base_url.replace('/v1', '') + '/api/tags'
        
        try:
            logger.info(f"Validating Ollama connection to: {health_url}")
            
            # Use requests for synchronous connection check during initialization
            response = requests.get(health_url, timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama service returned status {response.status_code}")
                
            # Also check if the specific model is available
            models_data = response.json()
            available_models = [model.get('name', '') for model in models_data.get('models', [])]
            available_model_names = [model.split(':')[0] for model in available_models]
            
            logger.info(f"Available models: {available_models}")
            
            # Check both full model name and base name
            model_found = (
                model_name in available_models or 
                model_name.split(':')[0] in available_model_names
            )
            
            if not model_found:
                logger.warning(f"Model '{model_name}' not found in Ollama. Available models: {available_models}")
                logger.warning(f"You may need to download it with: ollama pull {model_name}")
                # Don't raise error, just warn - the model might still work
                
        except requests.exceptions.Timeout:
            raise ConnectionError("Ollama service is not responding (timeout)")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Cannot connect to Ollama service. Please ensure Ollama is running with 'ollama serve'")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Cannot connect to Ollama service: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Failed to validate Ollama connection: {str(e)}")
    
    async def stream_chat(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """Override stream_chat with Ollama native API handling."""
        # Circuit breaker: if too many consecutive failures, raise immediately
        if self._consecutive_failures >= self._max_consecutive_failures:
            raise ConnectionError(f"Ollama service appears to be down (failed {self._consecutive_failures} times). Please check the service and restart.")
        
        try:
            # Use Ollama native API instead of OpenAI compatibility
            async for chunk in self._stream_chat_native(messages):
                yield chunk
            
            # Reset failure count on success
            self._consecutive_failures = 0
            
        except Exception as e:
            self._consecutive_failures += 1
            error_msg = str(e).lower()
            
            logger.error(f"Ollama stream error (attempt {self._consecutive_failures}): {e}")
            
            if any(keyword in error_msg for keyword in ['connection', 'refused', 'unreachable', 'timeout', 'disconnected']):
                enhanced_msg = f"Ollama连接失败 (连续失败{self._consecutive_failures}次): {str(e)}"
                if self._consecutive_failures >= self._max_consecutive_failures:
                    enhanced_msg += f"\n建议: Ollama服务可能已停止，请检查服务状态并重启"
                else:
                    enhanced_msg += f"\n建议: 请确保Ollama服务正在运行 (ollama serve)"
                raise ConnectionError(enhanced_msg)
            else:
                raise ConnectionError(f"Ollama错误: {str(e)}")
    
    async def _stream_chat_native(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """Use Ollama's native API for streaming with enhanced logging."""
        import json
        import aiohttp
        
        # Convert messages to a single prompt for Ollama native API
        cleaned_messages = validate_and_clean_messages(messages)
        
        if not cleaned_messages:
            raise ValueError("No valid messages to send")
        
        # Convert chat messages to prompt format
        prompt_parts = []
        for msg in cleaned_messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        # Add assistant prompt
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)
        
        # Use native Ollama API
        native_url = self.config.base_url.replace('/v1', '') + '/api/generate'
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        logger.info(f"Sending request to Ollama native API: {native_url}")
        logger.info(f"Using model: {self.config.model}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response_chunks = []
        total_response_content = ""
        in_think_block = False
        
        async with aiohttp.ClientSession() as session:
            async with session.post(native_url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API returned status {response.status}: {error_text}")
                    raise ConnectionError(f"Ollama API returned status {response.status}: {error_text}")
                
                logger.info("✅ Ollama API request successful, processing response stream...")
                
                async for line in response.content:
                    if line:
                        try:
                            line_str = line.decode('utf-8').strip()
                            if line_str:  # Skip empty lines
                                data = json.loads(line_str)
                                response_chunks.append(data)
                                
                                # Log the chunk data for debugging
                                logger.debug(f"Received chunk: {data}")
                                
                                if 'response' in data:
                                    chunk_content = data['response']
                                    if chunk_content:  # Only process non-empty chunks
                                        total_response_content += chunk_content
                                        
                                        # Update state and filter think blocks in real-time
                                        if '<think>' in chunk_content:
                                            in_think_block = True
                                            # Extract any content before <think> tag
                                            before_think = chunk_content.split('<think>')[0]
                                            if before_think and not in_think_block:
                                                logger.debug(f"Yielding content before think: '{before_think}'")
                                                yield before_think
                                        elif '</think>' in chunk_content:
                                            in_think_block = False
                                            # Extract any content after </think> tag
                                            after_think = chunk_content.split('</think>')[-1]
                                            if after_think:
                                                logger.debug(f"Yielding content after think: '{after_think}'")
                                                yield after_think
                                        elif not in_think_block:
                                            # Normal content outside think blocks
                                            logger.debug(f"Yielding normal chunk: '{chunk_content}'")
                                            yield chunk_content
                                            
                                    elif data.get('done', False):
                                        # This is the final chunk, might be empty
                                        logger.debug("Received final chunk (done=True)")
                                
                                if data.get('done', False):
                                    logger.info(f"✅ Ollama response complete. Total content length: {len(total_response_content)}")
                                    if total_response_content:
                                        logger.info(f"Response preview: {total_response_content[:200]}{'...' if len(total_response_content) > 200 else ''}")
                                    else:
                                        logger.warning("⚠️ Ollama response was empty!")
                                    break
                                    
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON from Ollama response: {e}, line: {line_str}")
                            continue
                
                # Final check - if we got no content at all, log detailed info
                if not total_response_content:
                    logger.error("❌ Ollama streaming completed but no content was received!")
                    logger.error(f"Total chunks received: {len(response_chunks)}")
                    if response_chunks:
                        logger.error(f"Sample chunks: {json.dumps(response_chunks[:3], indent=2, ensure_ascii=False)}")
                    
                    # Yield a placeholder message to indicate the problem
                    yield "[Ollama 响应为空 - 可能是模型配置问题或者模型正在加载中]"


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
        elif "ollama" in config.name or platform_name == "ollama":
            return OllamaClient(config)
        else:
            raise ValueError(f"Unsupported platform: {config.name}")
    
    @staticmethod
    def create_all_clients(platform_configs) -> List[BaseLLMClient]:
        """Create clients for all enabled platforms."""
        from .config import PlatformConfigs
        
        clients = []
        failed_clients = []
        
        for config in platform_configs.get_enabled_configs():
            try:
                logger.info(f"Creating client for {config.name}...")
                client = LLMClientFactory.create_client(config)
                clients.append(client)
                logger.info(f"✅ Successfully created client for {config.name}")
            except ConnectionError as e:
                # Special handling for connection errors (e.g., Ollama not running)
                error_msg = f"❌ {config.name} connection failed: {str(e)}"
                if "ollama" in config.name.lower():
                    error_msg += "\n💡 提示：请确保 Ollama 服务正在运行 (ollama serve)"
                logger.warning(error_msg)
                failed_clients.append((config.name, str(e)))
            except Exception as e:
                error_msg = f"❌ Failed to create client for {config.name}: {str(e)}"
                logger.error(error_msg)
                failed_clients.append((config.name, str(e)))
        
        if not clients:
            error_details = "\n".join([f"- {name}: {error}" for name, error in failed_clients])
            raise ValueError(f"No valid LLM clients could be created. Errors:\n{error_details}\n\n请检查您的配置和网络连接。")
        
        if failed_clients:
            logger.info(f"✅ Successfully created {len(clients)} clients. {len(failed_clients)} clients failed to initialize.")
        
        return clients 
"""LLM Chats - Multi-LLM conversation system."""

__version__ = "0.1.0"
__author__ = "LLM Chats"
__email__ = "llm-chats@example.com"
__description__ = "A service for multi-LLM conversations to explore topic understanding through discussion"

from .app import main, create_gradio_app
from .client import BaseLLMClient, LLMClientFactory, Message, ChatResponse
from .conversation import ConversationManager, ConversationConfig, ConversationState
from .config import get_config, PlatformConfigs, LLMConfig

__all__ = [
    "main",
    "create_gradio_app", 
    "BaseLLMClient",
    "LLMClientFactory",
    "Message",
    "ChatResponse",
    "ConversationManager",
    "ConversationConfig", 
    "ConversationState",
    "get_config",
    "PlatformConfigs",
    "LLMConfig",
]

def main() -> None:
    """Main entry point for the LLM Chats application."""
    from .app import main as app_main
    app_main()

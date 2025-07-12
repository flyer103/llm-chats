"""Gradio application for multi-LLM conversations."""
import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
import json

import gradio as gr

from .config import get_config
from .client import LLMClientFactory, Message
from .conversation import ConversationManager, ConversationConfig, ConversationState
from .file_processor import process_uploaded_file, format_file_content_for_context
from .summarizer import ConversationSummarizer, SummaryConfig
from .model_updater import ModelUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Back to INFO level for normal operation
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
conversation_manager: Optional[ConversationManager] = None
available_platforms: List[str] = []

# Global state for caching model information
_model_info_cache = {}
_model_info_cache_timestamp = 0
_model_info_cache_ttl = 300  # 5 minutes cache


def initialize_clients():
    """Initialize LLM clients with enhanced error reporting."""
    global conversation_manager, available_platforms
    
    try:
        config = get_config()
        
        if config.count_enabled() == 0:
            logger.warning("No LLM platforms are enabled. Check your environment variables.")
            return "⚠️ 未配置任何LLM平台，请检查环境变量设置"
        
        clients = LLMClientFactory.create_all_clients(config)
        
        if not clients:
            return "❌ 无法创建任何LLM客户端，请检查配置和网络连接"
        
        conversation_manager = ConversationManager(clients)
        available_platforms = [client.platform_name for client in clients]
        
        enabled_list = [client.platform_name for client in clients]
        
        # Provide additional status information
        total_configured = config.count_enabled()
        success_count = len(clients)
        failed_count = total_configured - success_count
        
        result_msg = f"✅ 成功初始化 {success_count} 个LLM平台: {', '.join(enabled_list)}"
        
        if failed_count > 0:
            result_msg += f"\n⚠️ {failed_count} 个平台初始化失败"
            
            # Add specific guidance for common issues
            if any("ollama" in platform.lower() for platform in [c.platform_name for c in clients] if "ollama" in platform.lower()):
                # Ollama succeeded
                pass
            else:
                # Ollama might have failed
                result_msg += "\n💡 如果Ollama初始化失败，请确保服务正在运行: ollama serve"
        
        return result_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to initialize clients: {e}")
        
        # Enhanced error messages with troubleshooting tips
        if "ollama" in error_msg.lower() and "connection" in error_msg.lower():
            return f"❌ 初始化失败: {error_msg}\n\n💡 故障排除:\n1. 启动Ollama服务: ollama serve\n2. 检查端口占用: lsof -i :11434\n3. 验证Ollama状态: curl http://localhost:11434/api/tags"
        elif "api key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return f"❌ 初始化失败: {error_msg}\n\n💡 故障排除:\n1. 检查API密钥是否正确配置\n2. 验证密钥是否有效且未过期\n3. 确认密钥权限设置"
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return f"❌ 初始化失败: {error_msg}\n\n💡 故障排除:\n1. 检查网络连接\n2. 验证防火墙设置\n3. 确认代理配置"
        else:
            return f"❌ 初始化失败: {error_msg}\n\n💡 建议: 请检查配置文件和环境变量设置"


async def test_platform_config(platform_name: str) -> str:
    """Test a specific platform configuration."""
    if not conversation_manager:
        return "❌ 请先初始化LLM客户端"
    
    if platform_name not in conversation_manager.clients:
        return f"❌ 平台 {platform_name} 未配置或未启用"
    
    try:
        client = conversation_manager.clients[platform_name]
        
        # 创建简单的测试消息
        test_messages = [Message(
            role="user",
            content="你好，请回复'测试成功'",
            timestamp=time.time()
        )]
        
        # 发送测试请求
        response = await client.chat(test_messages)
        
        if response.content:
            return f"✅ {platform_name} 配置正确，响应正常"
        else:
            return f"⚠️ {platform_name} 连接成功但响应为空"
            
    except Exception as e:
        error_str = str(e)
        
        if "404" in error_str and "NotFound" in error_str:
            if platform_name == "doubao":
                return f"❌ 火山豆包配置错误：请检查 DOUBAO_MODEL 是否为正确的endpoint ID"
            else:
                return f"❌ {platform_name} 模型不存在或无访问权限"
        elif "402" in error_str:
            return f"❌ {platform_name} 账户余额不足"
        elif "401" in error_str:
            return f"❌ {platform_name} API密钥无效"
        elif "429" in error_str:
            return f"⚠️ {platform_name} 请求频率超限，请稍后重试"
        else:
            return f"❌ {platform_name} 测试失败: {error_str[:100]}..."


def get_platform_model_info() -> Dict[str, str]:
    """Get model information for each platform with caching."""
    global _model_info_cache, _model_info_cache_timestamp
    
    current_time = time.time()
    
    # Check if we have valid cached data
    if (_model_info_cache and 
        current_time - _model_info_cache_timestamp < _model_info_cache_ttl):
        return _model_info_cache
    
    try:
        from .model_updater import ModelUpdater
        
        logger.info("Fetching latest model information...")
        updater = ModelUpdater()
        platforms_models = updater.get_all_platforms_models()
        
        model_info = {}
        platform_name_mapping = {
            'alibaba': '阿里云百炼',
            'doubao': '火山豆包', 
            'moonshot': '月之暗面',
            'deepseek': 'DeepSeek',
            'ollama': 'Ollama'
        }
        
        for platform_key, platform_data in platforms_models.items():
            platform_name = platform_name_mapping.get(platform_key, platform_data.platform)
            
            # Get top model for this platform
            top_models = platform_data.get_top_models(1)
            if top_models:
                model = top_models[0]
                # Format model info: Platform (Model Version)
                model_info[platform_name] = f"{platform_name} ({model.name})"
            else:
                model_info[platform_name] = platform_name
        
        # Cache the results
        _model_info_cache = model_info
        _model_info_cache_timestamp = current_time
        
        logger.info(f"Model information cached for {len(model_info)} platforms")
        return model_info
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        # Return cached data if available, otherwise fallback to basic platform names
        if _model_info_cache:
            logger.info("Using cached model information due to error")
            return _model_info_cache
        else:
            logger.info("Using fallback platform names")
            return {platform: platform for platform in available_platforms}


def refresh_model_info_cache():
    """Manually refresh the model information cache."""
    global _model_info_cache, _model_info_cache_timestamp
    
    # Clear cache to force refresh
    _model_info_cache = {}
    _model_info_cache_timestamp = 0
    
    # Get fresh model information
    return get_platform_model_info()


def get_platform_choices():
    """Get available platform choices for UI with model version info."""
    model_info = get_platform_model_info()
    
    # Filter to only include available platforms
    choices = []
    for platform in available_platforms:
        display_name = model_info.get(platform, platform)
        choices.append((display_name, platform))
    
    return choices


def get_summary_model_choices():
    """Get available summary model choices with model version info."""
    model_info = get_platform_model_info()
    
    # Create choices for summary models
    choices = []
    for platform in available_platforms:
        display_name = model_info.get(platform, platform)
        choices.append((display_name, platform))
    
    return choices


def process_uploaded_files(files) -> Tuple[List[Dict[str, Any]], str]:
    """
    Process uploaded files and return processing results.
    
    Args:
        files: List of uploaded file paths from Gradio
        
    Returns:
        Tuple of (processed_files_list, status_message)
    """
    if not files:
        return [], ""
    
    processed_files = []
    status_messages = []
    
    for file_path in files:
        if file_path is None:
            continue
            
        try:
            # Process the file
            result = process_uploaded_file(file_path)
            processed_files.append(result)
            
            # Generate status message
            file_info = result.get('file_info', {})
            file_name = file_info.get('name', 'unknown')
            
            if result['processing_status'] == 'success':
                word_count = result.get('word_count', 0)
                status_messages.append(f"✅ {file_name}: 成功提取 {word_count} 个词")
            else:
                error_msg = result.get('error', '未知错误')
                status_messages.append(f"❌ {file_name}: {error_msg}")
                
        except Exception as e:
            status_messages.append(f"❌ 处理文件失败: {str(e)}")
    
    status_text = "\n".join(status_messages) if status_messages else ""
    return processed_files, status_text


def create_conversation_with_files(topic: str, max_rounds: int, participants: List[str], 
                                  round_timeout: float, processed_files: List[Dict[str, Any]]) -> str:
    """Create a new conversation with file attachments."""
    if not conversation_manager:
        return "❌ 请先初始化LLM客户端"
    
    if not topic.strip():
        return "❌ 请输入讨论话题"
    
    if not participants:
        return "❌ 请选择至少一个参与平台"
    
    try:
        # Create enhanced topic with file context
        enhanced_topic = topic.strip()
        
        # Add file content to topic if files are processed
        if processed_files:
            file_contexts = []
            for file_data in processed_files:
                if file_data['processing_status'] == 'success':
                    file_context = format_file_content_for_context(file_data)
                    file_contexts.append(file_context)
            
            if file_contexts:
                enhanced_topic += "\n\n" + "\n\n".join(file_contexts)
        
        config = ConversationConfig(
            topic=enhanced_topic,
            max_rounds=max_rounds,
            round_timeout=round_timeout
        )
        
        conversation_id = conversation_manager.create_conversation(config, participants)
        
        file_summary = ""
        if processed_files:
            successful_files = [f for f in processed_files if f['processing_status'] == 'success']
            if successful_files:
                file_summary = f"，包含 {len(successful_files)} 个附件"
        
        return f"✅ 创建对话成功{file_summary}！对话ID: {conversation_id}"
        
    except Exception as e:
        logger.error(f"Failed to create conversation with files: {e}")
        return f"❌ 创建对话失败: {str(e)}"


def create_conversation(topic: str, max_rounds: int, participants: List[str], round_timeout: float) -> str:
    """Create a new conversation."""
    if not conversation_manager:
        return "❌ 请先初始化LLM客户端"
    
    if not topic.strip():
        return "❌ 请输入讨论话题"
    
    if not participants:
        return "❌ 请选择至少一个参与平台"
    
    try:
        config = ConversationConfig(
            topic=topic.strip(),
            max_rounds=max_rounds,
            round_timeout=round_timeout
        )
        
        conversation_id = conversation_manager.create_conversation(config, participants)
        return f"✅ 创建对话成功！对话ID: {conversation_id}"
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return f"❌ 创建对话失败: {str(e)}"


async def start_conversation_async(conversation_id: str, progress_callback=None):
    """Start conversation asynchronously."""
    if not conversation_manager:
        return "❌ 对话管理器未初始化"
    
    try:
        conversation = await conversation_manager.start_conversation(conversation_id, progress_callback)
        return conversation
    except Exception as e:
        logger.error(f"Conversation failed: {e}")
        raise


def format_conversation_display(conversation, streaming_content=None, progress_info=None) -> str:
    """Format conversation for display with streaming support."""
    if not conversation:
        return "🔍 未找到对话记录"
    
    output = []
    
    # Fixed header with discussion topic, participants, and status
    output.append('<div class="fixed-header">')
    output.append('<div class="fixed-header-content">')
    
    # Participants in fixed header
    output.append(f'<div class="discussion-participants">👥 参与者: {", ".join(conversation.participants)}</div>')
    
    # Enhanced status with progress info
    if progress_info:
        # Use dynamic progress information
        status_text = f"📊 状态: {progress_info['status']} | 🔄 轮次: {progress_info['current_round']}/{progress_info['total_rounds']}"
    else:
        # Fallback to static status
        status_text = f"📊 状态: {conversation.state.value} | 🔄 轮次: {len(conversation.rounds)}/{conversation.config.max_rounds}"
    
    output.append(f'<div class="discussion-metadata">{status_text}</div>')
    
    output.append('</div>')  # End fixed-header-content
    output.append('</div>')  # End fixed-header
    
    # Conversation content area
    output.append('<div class="conversation-content">')
    output.append("")
    
    if not conversation.rounds:
        output.append("⏳ 等待对话开始...")
        # 但仍然需要检查是否有流式内容需要显示
        if streaming_content:
            output.append("")
            output.append("---")
            output.append("")
            # 显示第一轮的流式内容
            output.append("## 🔄 第 1 轮")
            output.append("⏳ 本轮对话进行中...")
            output.append("")
            output.append("### 💬 正在回复中...")
            output.append("")
            
            # 平台图标映射
            platform_emoji = {
                "阿里云百炼": "🔵",
                "火山豆包": "🔴", 
                "月之暗面": "🌙",
                "DeepSeek": "🤖",
                "Ollama": "🏠"
            }
            
            for platform, content in streaming_content.items():
                if content and content.strip():
                    emoji = platform_emoji.get(platform, "💬")
                    output.append(f"#### {emoji} {platform}")
                    output.append(f'<div class="streaming-content">{content}</div>')
                    # 添加光标指示符表示正在输入
                    output.append("")
                    output.append('<span class="typing-cursor">▋</span> *正在输入中...*')
                    output.append("")
            
            output.append("---")
            output.append("")
        else:
            # Close conversation-content container
            output.append("</div>")  # End conversation-content
            return "\n".join(output)
    
    # 平台图标映射
    platform_emoji = {
        "阿里云百炼": "🔵",
        "火山豆包": "🔴", 
        "月之暗面": "🌙",
        "DeepSeek": "🤖",
        "Ollama": "🏠"
    }
    
    for round_obj in conversation.rounds:
        output.append(f"## 🔄 第 {round_obj.round_number} 轮")
        if round_obj.duration:
            output.append(f"*⏱️ 耗时: {round_obj.duration:.1f}秒*")
        output.append("")
        
        if not round_obj.messages:
            output.append("⏳ 本轮对话进行中...")
            output.append("")
            
            # 如果这是最后一轮(正在进行的轮次)且有流式内容，显示在这里
            if round_obj.round_number == len(conversation.rounds) and streaming_content:
                output.append("### 💬 正在回复中...")
                output.append("")
                
                for platform, content in streaming_content.items():
                    if content and content.strip():
                        emoji = platform_emoji.get(platform, "💬")
                        output.append(f"#### {emoji} {platform}")
                        output.append(f'<div class="streaming-content">{content}</div>')
                        # 添加光标指示符表示正在输入
                        output.append("")
                        output.append('<span class="typing-cursor">▋</span> *正在输入中...*')
                        output.append("")
        else:
            for msg in round_obj.messages:
                if msg.role == "assistant":
                    emoji = platform_emoji.get(msg.platform, "💬")
                    output.append(f"### {emoji} {msg.platform}")
                    
                    # 确保内容不为空
                    content = msg.content if msg.content else "💭 [正在思考...]"
                    output.append(content)
                    
                    # 添加参考链接显示
                    if msg.has_references():
                        output.append("")
                        output.append("📚 参考链接:")
                        for ref in msg.references or []:
                            title = ref.get('title', '未知标题')
                            url = ref.get('url', '#')
                            description = ref.get('description', '')
                            
                            if description:
                                output.append(f"- 🔗 [{title}]({url}): {description}")
                            else:
                                output.append(f"- 🔗 [{title}]({url})")
                    
                    output.append("")
        
        output.append("---")
        output.append("")
    
    # Close conversation-content container
    output.append("</div>")  # End conversation-content
    
    return "\n".join(output)


def run_conversation(topic: str, max_rounds: int, participants: List[str], 
                    round_timeout: float):
    """Run a complete conversation workflow with streaming support."""
    if not conversation_manager:
        yield "❌ 请先初始化LLM客户端"
        return
    
    # Create conversation
    create_result = create_conversation(topic, max_rounds, participants, round_timeout)
    if create_result.startswith("❌"):
        yield create_result
        return
    
    # Extract conversation ID
    conversation_id = create_result.split("ID: ")[1]
    
    yield f"开始讨论话题: {topic}"
    
    # Progress tracking - 增强流式内容跟踪
    progress_info = {
        "current_round": 0,
        "total_rounds": max_rounds,
        "current_platform": "",
        "status": "准备中...",
        "streaming_content": {},  # Store streaming content for each platform
        "active_streaming": False,  # Track if currently streaming
        "last_update": time.time()
    }
    
    def update_progress(event_type: str, data: Dict[str, Any]):
        current_time = time.time()
        
        if event_type == "round_start":
            progress_info["current_round"] = data["round"]
            progress_info["status"] = f"第 {data['round']} 轮开始"
            progress_info["streaming_content"] = {}
            progress_info["active_streaming"] = False
            # Force update to show the new round
            progress_info["force_update"] = True
        elif event_type == "participant_thinking":
            progress_info["current_platform"] = data["platform"]
            if data.get("fallback_reason") == "streaming_failed":
                progress_info["status"] = f"{data['platform']} 流式连接失败，尝试常规模式..."
            else:
                progress_info["status"] = f"{data['platform']} 思考中..."
            progress_info["streaming_content"][data["platform"]] = ""
            progress_info["active_streaming"] = False
            # Force update to show thinking status
            progress_info["force_update"] = True
        elif event_type == "participant_streaming":
            platform = data["platform"]
            progress_info["current_platform"] = platform
            progress_info["status"] = f"{platform} 回复中..."
            progress_info["streaming_content"][platform] = data["partial_content"]
            progress_info["active_streaming"] = True
            progress_info["last_update"] = current_time
            # Mark for immediate update
            progress_info["force_update"] = True
        elif event_type == "participant_response":
            platform = data["platform"]
            progress_info["status"] = f"{data['platform']} 回复完成"
            # Keep the final content in streaming_content for a moment to allow final UI update
            # Clear the streaming content for this specific platform
            if platform in progress_info["streaming_content"]:
                del progress_info["streaming_content"][platform]
            # Only set active_streaming to False if no other platforms are streaming
            if not progress_info["streaming_content"]:
                progress_info["active_streaming"] = False
            # Force update to show completion status
            progress_info["force_update"] = True
        elif event_type == "participant_timeout":
            platform = data["platform"]
            timeout_duration = data["timeout_duration"]
            progress_info["current_platform"] = platform
            progress_info["status"] = f"{platform} 响应超时 ({timeout_duration}s)"
            # Clear the streaming content for this platform
            if platform in progress_info["streaming_content"]:
                del progress_info["streaming_content"][platform]
            if not progress_info["streaming_content"]:
                progress_info["active_streaming"] = False
            # Force update to show timeout status
            progress_info["force_update"] = True
        elif event_type == "round_complete":
            progress_info["status"] = f"第 {data['round']} 轮完成 (耗时: {data['duration']:.1f}s)"
            progress_info["streaming_content"] = {}
            progress_info["active_streaming"] = False
            # Force update to show the completed round
            progress_info["force_update"] = True
    
    # Start conversation
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_with_progress():
            conversation = await start_conversation_async(conversation_id, update_progress)
            return conversation
        
        # Run conversation with periodic updates
        task = loop.create_task(run_with_progress())
        
        # Track last update time for more responsive streaming
        last_update_time = time.time()
        last_streaming_content = {}
        
        while not task.done():
            current_time = time.time()
            
            # Update progress display - compact format
            # progress_text = f"{progress_info['current_round']}/{progress_info['total_rounds']} 轮 | {progress_info['status']}"
            
            # Get current conversation state
            current_conv = conversation_manager.get_conversation(conversation_id)
            
            # Format display with streaming content and progress info
            streaming_content = progress_info["streaming_content"] if progress_info["active_streaming"] else None
            conversation_display = format_conversation_display(current_conv, streaming_content, progress_info) if current_conv else ""
            
            # Force update if streaming content has changed or enough time has passed
            should_update = False
            
            if progress_info["active_streaming"]:
                # Check if streaming content has changed
                if streaming_content != last_streaming_content:
                    should_update = True
                    last_streaming_content = streaming_content.copy() if streaming_content else {}
                # Or if enough time has passed (minimum 0.1s for streaming)
                elif current_time - last_update_time >= 0.1:
                    should_update = True
            else:
                # Non-streaming: update every 0.5s
                if current_time - last_update_time >= 0.5:
                    should_update = True
            
            # Always update if status changed significantly
            if not hasattr(progress_info, '_last_status') or progress_info['status'] != progress_info.get('_last_status'):
                should_update = True
                progress_info['_last_status'] = progress_info['status']
            
            # Check for force update flag
            if progress_info.get("force_update", False):
                should_update = True
                progress_info["force_update"] = False
            
            if should_update:
                yield conversation_display
                last_update_time = current_time
            
            # Dynamic sleep - very short for responsive UI
            if progress_info["active_streaming"]:
                # Very frequent updates during streaming
                loop.run_until_complete(asyncio.sleep(0.01))
            else:
                # Still responsive when not streaming
                loop.run_until_complete(asyncio.sleep(0.1))
        
        # Get final result
        final_conversation = task.result()
        final_display = format_conversation_display(final_conversation)
        
        yield final_display
        
    except Exception as e:
        error_msg = f"❌ 讨论过程中发生错误: {str(e)}"
        logger.error(error_msg)
        yield error_msg
    finally:
        loop.close()


def export_conversation(conversation_id: str) -> str:
    """Export conversation to JSON."""
    if not conversation_manager or not conversation_id:
        return "请提供有效的对话ID"
    
    try:
        json_data = conversation_manager.export_conversation(conversation_id)
        return json_data
    except Exception as e:
        return f"导出失败: {str(e)}"


def create_gradio_app() -> gr.Blocks:
    """Create the Gradio application."""
    
    # Import professional UI components
    from .ui_components import ProfessionalTheme, ProfessionalLayout, ConversationCard, StatusIndicator
    
    with gr.Blocks(
        title="🤖 LLM Chats - 多模型协作深度研究平台",
        css=ProfessionalTheme.get_css() + """
        /* Application-specific overrides */
        .gradio-container {
            max-width: 100% !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding: 20px !important;
        }
        
        /* Main conversation display area - will use component styles */
        
        /* Typing cursor animation */
        .typing-cursor {
            animation: blink 1s infinite;
            color: var(--primary-color);
            font-weight: bold;
        }
        
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0; }
            100% { opacity: 1; }
        }
        }
        
        /* Dark mode specific overrides */
        @media (prefers-color-scheme: dark) {
            .gradio-container {
                background-color: #1a1a1a !important;
            }
            
            /* Ensure buttons are visible in dark mode */
            .gradio-container .gr-button {
                color: var(--text-color) !important;
            }
            
            /* Labels and form elements */
            .gradio-container label {
                color: var(--text-color) !important;
            }
            
            /* Checkboxes and radio buttons */
            .gradio-container .gr-checkbox,
            .gradio-container .gr-radio {
                color: var(--text-color) !important;
            }
            
            /* Input fields and textareas */
            .gradio-container input,
            .gradio-container textarea,
            .gradio-container select {
                color: var(--text-color) !important;
                background-color: #2a2a2a !important;
                border-color: var(--border-color) !important;
            }
            
            /* Placeholder text */
            .gradio-container input::placeholder,
            .gradio-container textarea::placeholder {
                color: #888888 !important;
            }
            
            /* Gradio specific elements */
            .gradio-container .gr-form,
            .gradio-container .gr-box,
            .gradio-container .gr-panel {
                background-color: #2a2a2a !important;
            }
            
            /* Markdown and text content */
            .gradio-container .gr-markdown {
                color: var(--text-color) !important;
            }
            
            /* Slider components */
            .gradio-container .gr-slider {
                color: var(--text-color) !important;
            }
            
            /* Checkbox group items */
            .gradio-container .gr-checkbox-group label {
                color: var(--text-color) !important;
            }
            
            /* Force all text to be visible in dark mode */
            .gradio-container *:not(button):not(input[type="button"]):not(input[type="submit"]) {
                color: #e0e0e0 !important;
            }
            
            /* Specific override for very stubborn elements */
            .gradio-container [data-testid] *,
            .gradio-container .svelte-* {
                color: #e0e0e0 !important;
            }
        }
        
        /* Browser-specific dark mode detection */
        html[data-color-mode="dark"] .gradio-container *,
        html[data-theme="dark"] .gradio-container *,
        [data-bs-theme="dark"] .gradio-container *,
        .dark .gradio-container *,
        body.dark .gradio-container * {
            color: #e0e0e0 !important;
        }
        
        /* High specificity override for any remaining dark text */
        .gradio-container *[style*="color"]:not([style*="color: rgb(224, 224, 224)"]):not([style*="color: #e0e0e0"]) {
            color: var(--text-color) !important;
        }
        """
    ) as app:
        
        # Professional header
        ProfessionalLayout.create_header()
        
        gr.Markdown("让不同的AI模型就同一话题进行深入讨论，探索通过多方对话理解话题的效果。")
        
        with gr.Row():
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("## ⚙️ 系统配置")
                
                init_btn = gr.Button("初始化LLM客户端", variant="primary")
                init_status = gr.Textbox(
                    label="初始化状态",
                    value="点击上方按钮初始化LLM客户端",
                    interactive=False
                )
                
                gr.Markdown("## 🎯 对话设置")
                
                topic_input = gr.Textbox(
                    label="讨论话题",
                    placeholder="例如：人工智能对未来社会的影响",
                    lines=3
                )
                
                # File upload section
                gr.Markdown("## 📎 文件上传")
                
                file_upload = gr.File(
                    label="上传附件 (支持PDF、图片等)",
                    file_count="multiple",
                    file_types=[".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"],
                    visible=True
                )
                
                file_status = gr.Textbox(
                    label="文件处理状态",
                    interactive=False,
                    visible=False,
                    lines=3
                )
                
                process_files_btn = gr.Button("处理文件", variant="secondary", visible=False)
                
                with gr.Row():
                    max_rounds = gr.Slider(
                        label="最大轮次",
                        minimum=1,
                        maximum=20,
                        value=5,
                        step=1
                    )
                    
                    round_timeout = gr.Slider(
                        label="单轮超时(秒)",
                        minimum=30,
                        maximum=300,
                        value=60,
                        step=10
                    )
                
                participants = gr.CheckboxGroup(
                    label="参与平台",
                    choices=[],  # Will be updated after initialization
                    value=[]
                )
                
                with gr.Row():
                    test_btn = gr.Button("测试配置", variant="secondary")
                    start_btn = gr.Button("开始讨论", variant="primary", size="lg")
                
                test_result = gr.Textbox(
                    label="配置测试结果",
                    lines=3,
                    interactive=False,
                    visible=False
                )
                
            with gr.Column(scale=3, min_width=600):
                # Simplified conversation display - no card container
                conversation_display = gr.Markdown(
                    value="",
                    elem_classes=["conversation-display"],
                    elem_id="conversation-display"
                )
                
                # Summary section
                gr.Markdown("## 📝 对话总结")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        summary_model = gr.Dropdown(
                            label="总结模型",
                            choices=[],
                            value=None,
                            info="选择用于生成总结的模型"
                        )
                        
                        with gr.Row():
                            summary_style = gr.Dropdown(
                                label="文章风格",
                                choices=[("学术研究", "academic"), ("博客文章", "blog"), ("研究报告", "report")],
                                value="academic",
                                info="选择总结文章的风格"
                            )
                            
                            summary_format = gr.Dropdown(
                                label="输出格式",
                                choices=[("Markdown", "markdown"), ("HTML", "html"), ("JSON", "json")],
                                value="markdown",
                                info="选择总结的输出格式"
                            )
                        
                        include_stats = gr.Checkbox(
                            label="包含统计信息",
                            value=True,
                            info="是否在总结中包含对话统计信息"
                        )
                        
                        with gr.Row():
                            generate_summary_btn = gr.Button(
                                "生成总结",
                                variant="primary",
                                size="lg"
                            )
                            
                            export_summary_btn = gr.Button(
                                "导出总结",
                                variant="secondary",
                                interactive=False
                            )
                            
                            update_models_btn = gr.Button(
                                "更新模型",
                                variant="secondary"
                            )
                    
                    with gr.Column(scale=1):
                        summary_status = gr.Textbox(
                            label="总结状态",
                            value="等待生成总结...",
                            interactive=False,
                            lines=3
                        )
                        
                        update_status = gr.Textbox(
                            label="模型更新状态",
                            value="",
                            interactive=False,
                            lines=3,
                            visible=False
                        )
                
                summary_display = gr.Markdown(
                    value="",
                    label="总结结果",
                    elem_classes=["conversation-display"]
                )
        
        # Global state for processed files
        processed_files_state = []
        
        # Global state for summary
        current_summary_result = None
        
        # Event handlers
        def update_init_and_choices():
            result = initialize_clients()
            
            # Pre-fetch model information for better UX
            if "✅ 成功初始化" in result:
                try:
                    get_platform_model_info()  # This will cache the model info
                except Exception as e:
                    logger.error(f"Failed to prefetch model info: {e}")
            
            choices = get_platform_choices()
            # Also update summary model choices
            summary_choices = get_summary_model_choices()
            return result, gr.update(choices=choices, value=[]), gr.update(choices=summary_choices, value=summary_choices[0][1] if summary_choices else None)
        
        def handle_file_upload(files):
            """Handle file upload and processing."""
            nonlocal processed_files_state
            
            if not files:
                processed_files_state = []
                return gr.update(visible=False), gr.update(visible=False)
            
            # Process files
            processed_files_state, status_text = process_uploaded_files(files)
            
            if status_text:
                return gr.update(value=status_text, visible=True), gr.update(visible=True)
            else:
                return gr.update(visible=False), gr.update(visible=False)
        
        def run_conversation_with_files(topic: str, max_rounds: int, participants: List[str], 
                                round_timeout: float):
            """Run conversation with file integration."""
            nonlocal processed_files_state
            
            # If there are processed files, integrate them into the topic
            if processed_files_state:
                file_contexts = []
                for processed_file in processed_files_state:
                    file_context = format_file_content_for_context(processed_file)
                    file_contexts.append(file_context)
                
                if file_contexts:
                    enhanced_topic = f"{topic}\n\n" + "\n\n".join(file_contexts)
                else:
                    enhanced_topic = topic
            else:
                enhanced_topic = topic
            
            # Create conversation
            if not conversation_manager:
                yield "❌ 请先初始化LLM客户端"
                return
            
            creation_result = create_conversation(enhanced_topic, max_rounds, participants, round_timeout)
            
            if not creation_result.startswith("✅"):
                yield creation_result
                return
            
            # Extract conversation ID
            conversation_id = creation_result.split("ID: ")[1]
            
            if not conversation_id:
                yield "❌ 无法获取对话ID"
                return
            
            # Start the conversation
            yield from run_conversation(enhanced_topic, max_rounds, participants, round_timeout)
        
        async def test_all_platforms(selected_platforms):
            """Test all selected platform configurations."""
            if not selected_platforms:
                return gr.update(value="请先选择要测试的平台", visible=True)
            
            results = []
            for platform in selected_platforms:
                result = await test_platform_config(platform)
                results.append(result)
            
            return gr.update(value="\n".join(results), visible=True)
        
        async def generate_summary(model_name, style, format_type, include_statistics):
            """Generate conversation summary."""
            nonlocal current_summary_result
            
            if not conversation_manager:
                return "❌ 请先初始化LLM客户端", "", gr.update(interactive=False)
            
            # Get the most recent completed conversation
            conversations = conversation_manager.list_conversations()
            completed_conversations = [c for c in conversations if c.state == ConversationState.COMPLETED]
            
            if not completed_conversations:
                return "❌ 没有找到已完成的对话", "", gr.update(interactive=False)
            
            # Get the most recent conversation
            conversation = max(completed_conversations, key=lambda c: c.updated_at)
            
            if not model_name:
                return "❌ 请选择总结模型", "", gr.update(interactive=False)
            
            try:
                # Create summarizer
                # conversation_manager is already checked above, so we can safely access it
                assert conversation_manager is not None  # Type assertion for mypy
                summarizer = ConversationSummarizer(conversation_manager.clients)
                
                # Create summary configuration - no length restrictions
                config = SummaryConfig(
                    output_format=format_type,
                    include_metadata=True,
                    include_statistics=include_statistics,
                    language="zh",
                    article_style=style
                )
                
                # Generate summary
                summary_result = await summarizer.generate_summary(conversation, model_name, config)
                current_summary_result = summary_result
                
                return f"✅ 总结生成成功！使用模型: {model_name}", summary_result.content, gr.update(interactive=True)
                
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                return f"❌ 生成总结失败: {str(e)}", "", gr.update(interactive=False)
        
        def export_summary():
            """Export the current summary."""
            if not current_summary_result:
                return "❌ 没有可导出的总结"
            
            try:
                # Create summarizer to use export function
                if not conversation_manager:
                    return "❌ 对话管理器未初始化"
                summarizer = ConversationSummarizer(conversation_manager.clients)
                result = summarizer.export_summary(current_summary_result)
                return result
            except Exception as e:
                return f"❌ 导出失败: {str(e)}"
        
        def update_models():
            """Update model configurations."""
            try:
                updater = ModelUpdater()
                # Get all platform models
                platforms_models = updater.get_all_platforms_models()
                
                # Update env.example file
                result = updater.update_env_example(platforms_models)
                
                # Generate models report
                report = updater.generate_models_report(platforms_models)
                
                # Refresh model info cache after update
                refresh_model_info_cache()
                
                return result, gr.update(value=report, visible=True)
                
            except Exception as e:
                logger.error(f"Failed to update models: {e}")
                return f"❌ 更新失败: {str(e)}", gr.update(visible=False)
        
        init_btn.click(
            fn=update_init_and_choices,
            outputs=[init_status, participants, summary_model]
        )
        
        test_btn.click(
            fn=test_all_platforms,
            inputs=[participants],
            outputs=[test_result]
        )
        
        # File upload event handlers
        file_upload.upload(
            fn=handle_file_upload,
            inputs=[file_upload],
            outputs=[file_status, process_files_btn]
        )
        
        start_btn.click(
            fn=run_conversation_with_files,
            inputs=[topic_input, max_rounds, participants, round_timeout],
            outputs=[conversation_display]
        )
        
        # Summary event handlers
        generate_summary_btn.click(
            fn=generate_summary,
            inputs=[summary_model, summary_style, summary_format, include_stats],
            outputs=[summary_status, summary_display, export_summary_btn]
        )
        
        export_summary_btn.click(
            fn=export_summary,
            outputs=[summary_status]
        )
        
        update_models_btn.click(
            fn=update_models,
            outputs=[summary_status, update_status]
        )
        
        # Initialize on startup
        app.load(
            fn=update_init_and_choices,
            outputs=[init_status, participants, summary_model]
        )
        
        # Add JavaScript for professional UI enhancements
        app.load(
            None, 
            None, 
            None, 
            js=ProfessionalTheme.get_js() + """
            // Additional application-specific JavaScript
            (function() {
                setTimeout(function() {
                    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                    
                    if (isDarkMode) {
                        const style = document.createElement('style');
                        style.id = 'dark-mode-override';
                        style.textContent = '.gradio-container *, .gradio-container input, .gradio-container textarea, .gradio-container label { color: #e0e0e0 !important; } .gradio-container input::placeholder, .gradio-container textarea::placeholder { color: #888 !important; }';
                        document.head.appendChild(style);
                    }
                }, 1000);
            })();
            """
        )
    
    return app


def main():
    """Main entry point for the application."""
    import os
    import socket
    
    print("🚀 启动 LLM Chats 多方对话系统...")
    
    # Disable all Gradio external connections
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    os.environ["GRADIO_SERVER_NAME"] = "127.0.0.1"
    os.environ["GRADIO_SHARE"] = "False"
    
    # Disable telemetry and external requests
    for key in ["HF_HUB_DISABLE_TELEMETRY", "DISABLE_TELEMETRY", "DO_NOT_TRACK"]:
        os.environ[key] = "1"
    
    def check_port(port):
        """Check if port is available."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) != 0
    
    # Find available port
    port = 7860
    while not check_port(port) and port < 7870:
        port += 1
    
    if port >= 7870:
        print("❌ 端口7860-7869都被占用，请释放端口后重试")
        return
    
    app = create_gradio_app()
    
    # Launch strategies in order of preference
    launch_strategies = [
        # Strategy 1: Local with 127.0.0.1
        {
            "server_name": "127.0.0.1",
            "server_port": port,
            "share": False,
            "quiet": True,
            "show_error": False,
            "inbrowser": False,
            "enable_monitoring": False
        },
        # Strategy 2: Local with localhost
        {
            "server_name": "localhost", 
            "server_port": port,
            "share": False,
            "quiet": True,
            "show_error": False,
            "inbrowser": False
        },
        # Strategy 3: Share link as fallback
        {
            "server_port": port,
            "share": True,
            "quiet": True,
            "show_error": False,
            "inbrowser": False
        },
        # Strategy 4: Minimal parameters
        {
            "share": True,
            "quiet": True
        }
    ]
    
    for i, strategy in enumerate(launch_strategies, 1):
        try:
            print(f"🔄 尝试启动方式 {i}/{len(launch_strategies)}...")
            
            # Filter out unsupported parameters
            valid_params = {}
            for key, value in strategy.items():
                try:
                    # Try to pass the parameter and see if it's accepted
                    valid_params[key] = value
                except:
                    continue
            
            app.launch(**valid_params)
            
            # If we get here, launch was successful
            if strategy.get("share", False):
                print("✅ 应用已启动！使用共享链接访问")
            else:
                print(f"✅ 应用已启动！访问地址: http://{strategy.get('server_name', '127.0.0.1')}:{strategy.get('server_port', port)}")
            
            print("⏹️  按 Ctrl+C 停止服务")
            break
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"   ❌ 方式 {i} 失败: {e}")
            
            # If it's the last strategy, show detailed error info
            if i == len(launch_strategies):
                print("\n🔧 所有启动方式都失败了，故障排除建议:")
                print("1. 检查网络连接和代理设置")
                print("2. 尝试关闭VPN或代理")
                print("3. 检查防火墙设置")
                print("4. 尝试不同端口: export PORT=8080 && python -m llm_chats")
                print("5. 使用简单启动: python -c \"import gradio as gr; gr.Interface(lambda x: x, 'text', 'text').launch()\"")
                raise
            
            continue


if __name__ == "__main__":
    main() 
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Back to INFO level for normal operation
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
conversation_manager: Optional[ConversationManager] = None
available_platforms: List[str] = []


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


def get_platform_choices():
    """Get available platform choices for UI."""
    return [(platform, platform) for platform in available_platforms]


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


def format_conversation_display(conversation, streaming_content=None) -> str:
    """Format conversation for display with streaming support."""
    if not conversation:
        return "🔍 未找到对话记录"
    
    output = []
    output.append(f"# 🎯 讨论话题: {conversation.config.topic}")
    output.append(f"**👥 参与者**: {', '.join(conversation.participants)}")
    output.append(f"**📊 状态**: {conversation.state.value}")
    output.append(f"**🔄 轮次**: {len(conversation.rounds)}/{conversation.config.max_rounds}")
    output.append("")
    output.append("---")
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
                    output.append("")
        
        output.append("---")
        output.append("")
    

    
    return "\n".join(output)


def run_conversation(topic: str, max_rounds: int, participants: List[str], 
                    round_timeout: float, progress_display):
    """Run a complete conversation workflow with streaming support."""
    if not conversation_manager:
        yield "❌ 请先初始化LLM客户端", ""
        return
    
    # Create conversation
    create_result = create_conversation(topic, max_rounds, participants, round_timeout)
    if create_result.startswith("❌"):
        yield create_result, ""
        return
    
    # Extract conversation ID
    conversation_id = create_result.split("ID: ")[1]
    
    yield f"开始讨论话题: {topic}", ""
    
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
            
            # Update progress display
            progress_text = f"**进度**: {progress_info['current_round']}/{progress_info['total_rounds']} 轮\n"
            progress_text += f"**状态**: {progress_info['status']}\n"
            if progress_info['current_platform']:
                progress_text += f"**当前**: {progress_info['current_platform']}"
            
            # Get current conversation state
            current_conv = conversation_manager.get_conversation(conversation_id)
            
            # Format display with streaming content
            streaming_content = progress_info["streaming_content"] if progress_info["active_streaming"] else None
            conversation_display = format_conversation_display(current_conv, streaming_content) if current_conv else ""
            
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
                yield progress_text, conversation_display
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
        
        yield "✅ 讨论完成！", final_display
        
    except Exception as e:
        error_msg = f"❌ 讨论过程中发生错误: {str(e)}"
        logger.error(f"Conversation error: {e}", exc_info=True)
        
        # 提供更详细的错误信息和解决建议
        if "No valid messages" in str(e):
            error_msg += "\n\n💡 建议：请检查选择的平台是否正确初始化"
        elif "timeout" in str(e).lower():
            error_msg += "\n\n💡 建议：请尝试增加超时时间或检查网络连接"
        elif "api" in str(e).lower():
            error_msg += "\n\n💡 建议：请检查API密钥和网络连接"
        
        yield error_msg, ""
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
    
    with gr.Blocks(
        title="LLM多方对话系统",
        css="""
        /* Force light text in dark mode - simplified approach */
        @media (prefers-color-scheme: dark) {
            .gradio-container,
            .gradio-container * {
                color: #e0e0e0 !important;
            }
            
            .gradio-container input,
            .gradio-container textarea {
                color: #e0e0e0 !important;
                background-color: #2a2a2a !important;
                border: 1px solid #555 !important;
            }
            
            .gradio-container input::placeholder,
            .gradio-container textarea::placeholder {
                color: #888 !important;
            }
            
            .gradio-container .conversation-display {
                background-color: #2a2a2a !important;
                color: #e0e0e0 !important;
            }
        }
        
        /* Root variables for theming */
        :root {
            --text-color: #333333;
            --bg-color: #f9f9f9;
            --border-color: #ddd;
            --streaming-bg: #e8f4f8;
            --error-color: #d32f2f;
            --error-bg: #ffebee;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            :root {
                --text-color: #e0e0e0;
                --bg-color: #2a2a2a;
                --border-color: #555;
                --streaming-bg: #1a3a4a;
                --error-color: #ff6b6b;
                --error-bg: #4a1a1a;
            }
        }
        
        .gradio-container {
            max-width: 100% !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding: 20px !important;
        }
        
        /* Main conversation display area */
        .conversation-display {
            max-height: 70vh;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            background-color: var(--bg-color);
            color: var(--text-color) !important;
        }
        
        /* Streaming content animation */
        .streaming-content {
            position: relative;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        /* Typing cursor animation */
        .typing-cursor {
            animation: blink 1s infinite;
            color: #007bff;
            font-weight: bold;
        }
        
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0; }
            100% { opacity: 1; }
        }
        .conversation-display * {
            color: var(--text-color) !important;
        }
        
        /* Streaming content styling */
        .streaming-content {
            background-color: var(--streaming-bg);
            border-left: 4px solid #0066cc;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            color: var(--text-color) !important;
        }
        
        /* Text elements styling */
        .gradio-container .markdown {
            color: var(--text-color) !important;
        }
        .gradio-container .markdown * {
            color: var(--text-color) !important;
        }
        .gradio-container .prose {
            color: var(--text-color) !important;
        }
        .gradio-container .prose * {
            color: var(--text-color) !important;
        }
        
        /* Input elements */
        .gradio-container .gr-textbox {
            color: var(--text-color) !important;
        }
        .gradio-container .gr-textbox textarea {
            color: var(--text-color) !important;
        }
        
        /* General text elements */
        .gradio-container p, 
        .gradio-container div, 
        .gradio-container span,
        .gradio-container h1,
        .gradio-container h2,
        .gradio-container h3,
        .gradio-container h4,
        .gradio-container h5,
        .gradio-container h6 {
            color: var(--text-color) !important;
        }
        
        /* Error message styling */
        .gradio-container .gr-error {
            color: var(--error-color) !important;
            background-color: var(--error-bg) !important;
        }
        
        /* Modal and alert styling */
        .gradio-container .gr-alert {
            color: var(--text-color) !important;
        }
        .gradio-container .gr-modal {
            color: var(--text-color) !important;
        }
        .gradio-container .gr-modal * {
            color: var(--text-color) !important;
        }
        
        /* Comprehensive text color override */
        .gradio-container * {
            color: var(--text-color) !important;
        }
        
        /* Force override any conflicting styles */
        .gradio-container [style*="color: white"],
        .gradio-container [style*="color: #ffffff"],
        .gradio-container [style*="color: black"],
        .gradio-container [style*="color: #000000"] {
            color: var(--text-color) !important;
        }
        
        /* Additional specific Gradio elements */
        .gradio-container .wrap,
        .gradio-container .block,
        .gradio-container .panel,
        .gradio-container .form,
        .gradio-container .gr-compact {
            color: var(--text-color) !important;
        }
        
        /* Input field specific styling */
        .gradio-container input[type="text"],
        .gradio-container input[type="email"],
        .gradio-container input[type="password"],
        .gradio-container input[type="number"] {
            color: var(--text-color) !important;
        }
        
        /* Ensure all text nodes are visible */
        .gradio-container [class*="label"],
        .gradio-container [class*="text"],
        .gradio-container [class*="title"],
        .gradio-container [class*="description"] {
            color: var(--text-color) !important;
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
        
        gr.Markdown("# 🤖 LLM多方对话系统")
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
                gr.Markdown("## 💬 对话进程")
                
                progress_display = gr.Markdown(
                    value="等待开始讨论...",
                    elem_classes=["conversation-display"]
                )
                
                conversation_display = gr.Markdown(
                    value="",
                    elem_classes=["conversation-display"]
                )
        
        # Event handlers
        def update_init_and_choices():
            result = initialize_clients()
            choices = get_platform_choices()
            return result, gr.update(choices=choices, value=[])
        
        async def test_all_platforms(selected_platforms):
            """Test all selected platform configurations."""
            if not selected_platforms:
                return gr.update(value="请先选择要测试的平台", visible=True)
            
            results = []
            for platform in selected_platforms:
                result = await test_platform_config(platform)
                results.append(result)
            
            return gr.update(value="\n".join(results), visible=True)
        
        init_btn.click(
            fn=update_init_and_choices,
            outputs=[init_status, participants]
        )
        
        test_btn.click(
            fn=test_all_platforms,
            inputs=[participants],
            outputs=[test_result]
        )
        
        start_btn.click(
            fn=run_conversation,
            inputs=[topic_input, max_rounds, participants, round_timeout, progress_display],
            outputs=[progress_display, conversation_display]
        )
        
        # Initialize on startup
        app.load(
            fn=update_init_and_choices,
            outputs=[init_status, participants]
        )
        
        # Add JavaScript for dark mode detection and text visibility
        app.load(
            None, 
            None, 
            None, 
            js="""
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
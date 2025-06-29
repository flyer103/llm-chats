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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
conversation_manager: Optional[ConversationManager] = None
available_platforms: List[str] = []


def initialize_clients():
    """Initialize LLM clients."""
    global conversation_manager, available_platforms
    
    try:
        config = get_config()
        
        if config.count_enabled() == 0:
            logger.warning("No LLM platforms are enabled. Check your environment variables.")
            return "⚠️ 未配置任何LLM平台，请检查环境变量设置"
        
        clients = LLMClientFactory.create_all_clients(config)
        
        if not clients:
            return "❌ 无法创建任何LLM客户端"
        
        conversation_manager = ConversationManager(clients)
        available_platforms = [client.platform_name for client in clients]
        
        enabled_list = [client.platform_name for client in clients]
        
        return f"✅ 成功初始化 {len(clients)} 个LLM平台: {', '.join(enabled_list)}"
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return f"❌ 初始化失败: {str(e)}"


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
    
    if len(participants) < 2:
        return "❌ 需要至少2个参与平台才能进行讨论"
    
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


def format_conversation_display(conversation) -> str:
    """Format conversation for display."""
    if not conversation:
        return "未找到对话记录"
    
    output = []
    output.append(f"# 讨论话题: {conversation.config.topic}")
    output.append(f"**参与者**: {', '.join(conversation.participants)}")
    output.append(f"**状态**: {conversation.state.value}")
    output.append(f"**轮次**: {len(conversation.rounds)}/{conversation.config.max_rounds}")
    output.append("---")
    
    for round_obj in conversation.rounds:
        output.append(f"## 第 {round_obj.round_number} 轮")
        if round_obj.duration:
            output.append(f"*耗时: {round_obj.duration:.1f}秒*")
        output.append("")
        
        for msg in round_obj.messages:
            if msg.role == "assistant":
                platform_emoji = {
                    "阿里云百炼": "🔵",
                    "火山豆包": "🔴", 
                    "月之暗面": "🌙",
                    "DeepSeek": "🤖"
                }
                emoji = platform_emoji.get(msg.platform, "💬")
                output.append(f"### {emoji} {msg.platform}")
                output.append(msg.content)
                output.append("")
        
        output.append("---")
    
    return "\n".join(output)


def run_conversation(topic: str, max_rounds: int, participants: List[str], 
                    round_timeout: float, progress_display):
    """Run a complete conversation workflow."""
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
    
    # Progress tracking
    progress_info = {
        "current_round": 0,
        "total_rounds": max_rounds,
        "current_platform": "",
        "status": "准备中..."
    }
    
    def update_progress(event_type: str, data: Dict[str, Any]):
        if event_type == "round_start":
            progress_info["current_round"] = data["round"]
            progress_info["status"] = f"第 {data['round']} 轮开始"
        elif event_type == "participant_thinking":
            progress_info["current_platform"] = data["platform"]
            progress_info["status"] = f"{data['platform']} 思考中..."
        elif event_type == "participant_response":
            progress_info["status"] = f"{data['platform']} 回复完成"
        elif event_type == "round_complete":
            progress_info["status"] = f"第 {data['round']} 轮完成 (耗时: {data['duration']:.1f}s)"
    
    # Start conversation
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_with_progress():
            conversation = await start_conversation_async(conversation_id, update_progress)
            return conversation
        
        # Run conversation with periodic updates
        task = loop.create_task(run_with_progress())
        
        while not task.done():
            # Update progress display
            progress_text = f"**进度**: {progress_info['current_round']}/{progress_info['total_rounds']} 轮\n"
            progress_text += f"**状态**: {progress_info['status']}\n"
            if progress_info['current_platform']:
                progress_text += f"**当前**: {progress_info['current_platform']}"
            
            # Get current conversation state
            current_conv = conversation_manager.get_conversation(conversation_id)
            conversation_display = format_conversation_display(current_conv) if current_conv else ""
            
            yield progress_text, conversation_display
            
            # Wait a bit before next update
            loop.run_until_complete(asyncio.sleep(1))
        
        # Get final result
        final_conversation = task.result()
        final_display = format_conversation_display(final_conversation)
        
        yield "✅ 讨论完成！", final_display
        
    except Exception as e:
        error_msg = f"❌ 讨论过程中发生错误: {str(e)}"
        logger.error(error_msg)
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
        .gradio-container {
            max-width: 1200px !important;
        }
        .conversation-display {
            max-height: 600px;
            overflow-y: auto;
        }
        """
    ) as app:
        
        gr.Markdown("# 🤖 LLM多方对话系统")
        gr.Markdown("让不同的AI模型就同一话题进行深入讨论，探索通过多方对话理解话题的效果。")
        
        with gr.Row():
            with gr.Column(scale=1):
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
                    lines=2
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
                
            with gr.Column(scale=2):
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
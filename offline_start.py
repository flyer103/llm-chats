#!/usr/bin/env python3
"""Completely offline startup script for LLM Chats."""

import os
import sys
from pathlib import Path

def main():
    """Start LLM Chats in completely offline mode."""
    print("🚀 启动 LLM Chats (完全离线模式)...")
    
    # Check if we're in the right directory
    if not Path("src/llm_chats").exists():
        print("❌ 错误：请在项目根目录运行此脚本")
        sys.exit(1)
    
    # Add src to path for imports
    sys.path.insert(0, str(Path("src")))
    
    # Set all possible environment variables to disable external connections
    offline_env = {
        "GRADIO_ANALYTICS_ENABLED": "False",
        "GRADIO_SHARE": "False",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "PYTHONHTTPSVERIFY": "0",
        "CURL_CA_BUNDLE": "",
        "REQUESTS_CA_BUNDLE": "",
    }
    
    for key, value in offline_env.items():
        os.environ[key] = value
    
    print("✅ 离线环境设置完成")
    
    try:
        import gradio as gr
        from llm_chats.config import get_config
        from llm_chats.client import LLMClientFactory
        from llm_chats.conversation import ConversationManager, ConversationConfig
        
        print("✅ 模块导入成功")
        
        # Create a simple interface that doesn't require external connections
        def simple_interface():
            """Create a simple gradio interface without external dependencies."""
            
            with gr.Blocks(title="LLM多方对话系统") as app:
                gr.Markdown("# 🤖 LLM多方对话系统 (离线模式)")
                gr.Markdown("系统正在离线模式下运行，部分功能可能受限。")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("## ⚙️ 系统状态")
                        status = gr.Textbox(
                            label="状态",
                            value="离线模式 - 请配置API密钥后刷新页面",
                            interactive=False
                        )
                        
                        gr.Markdown("## 🔧 配置")
                        gr.Markdown("请复制 `env.example` 到 `.env` 并填入API密钥")
                        
                        refresh_btn = gr.Button("刷新配置", variant="primary")
                        
                    with gr.Column():
                        gr.Markdown("## 📋 使用说明")
                        gr.Markdown("""
                        1. 配置API密钥后刷新页面
                        2. 等待系统初始化完成
                        3. 设置讨论话题和参数
                        4. 选择参与的AI平台
                        5. 开始多方对话
                        """)
                        
                        gr.Markdown("## 🔗 相关链接")
                        gr.Markdown("""
                        - [阿里云百炼](https://help.aliyun.com/zh/model-studio/)
                        - [火山豆包](https://www.volcengine.com/docs/82379/1399008)
                        - [月之暗面](https://platform.moonshot.cn/docs/intro)
                        - [DeepSeek](https://api-docs.deepseek.com/)
                        """)
                
                def check_config():
                    """Check configuration status."""
                    try:
                        config = get_config()
                        enabled = config.get_enabled_platforms()
                        if enabled:
                            return f"✅ 已配置 {len(enabled)} 个平台: {', '.join(enabled.keys())}"
                        else:
                            return "⚠️ 未配置任何平台，请设置环境变量"
                    except Exception as e:
                        return f"❌ 配置检查失败: {str(e)}"
                
                refresh_btn.click(
                    fn=check_config,
                    outputs=status
                )
                
                # Auto-check on load
                app.load(
                    fn=check_config,
                    outputs=status
                )
            
            return app
        
        # Create and launch the simple interface
        app = simple_interface()
        
        # Try different launch methods
        launch_methods = [
            {"server_name": "127.0.0.1", "server_port": 7860},
            {"server_name": "localhost", "server_port": 7860},
            {"server_port": 7861},
            {"share": True},
        ]
        
        for i, method in enumerate(launch_methods, 1):
            try:
                print(f"🔄 尝试启动方法 {i}: {method}")
                app.launch(quiet=True, **method)
                
                if method.get("share"):
                    print("✅ 应用已启动！使用共享链接访问")
                else:
                    host = method.get("server_name", "127.0.0.1")
                    port = method.get("server_port", 7860)
                    print(f"✅ 应用已启动！访问: http://{host}:{port}")
                
                print("⏹️  按 Ctrl+C 停止服务")
                break
                
            except Exception as e:
                print(f"   ❌ 方法 {i} 失败: {e}")
                if i == len(launch_methods):
                    raise
                continue
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("🔧 请安装依赖: uv sync")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 已停止服务")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 最后的解决方案:")
        print("1. 检查Python环境和依赖")
        print("2. 尝试重新安装: uv sync --reinstall")
        print("3. 手动测试: python -c \"import gradio; print('Gradio版本:', gradio.__version__)\"")
        sys.exit(1)

if __name__ == "__main__":
    main() 
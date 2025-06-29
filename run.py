#!/usr/bin/env python3
"""Simple startup script for LLM Chats."""

import sys
import os
from pathlib import Path

def main():
    """Start the LLM Chats application."""    
    # Check if we're in the right directory
    if not Path("src/llm_chats").exists():
        print("❌ 错误：请在项目根目录运行此脚本")
        sys.exit(1)
    
    # Set environment variables for offline mode
    offline_env = {
        "GRADIO_ANALYTICS_ENABLED": "False",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DISABLE_TELEMETRY": "1", 
        "DO_NOT_TRACK": "1"
    }
    
    for key, value in offline_env.items():
        os.environ[key] = value
    
    try:
        from llm_chats import main as app_main
        print("✅ 模块导入成功")
        print("🌐 正在启动Web界面...")
        print("-" * 50)
        
        app_main()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("🔧 请确保已安装依赖: uv sync")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 已停止LLM Chats服务")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查网络连接和代理设置")
        print("2. 尝试关闭VPN或防火墙")
        print("3. 使用不同方式启动:")
        print("   - uv run llm-chats")
        print("   - python main.py")
        print("   - python -m llm_chats")
        sys.exit(1)

if __name__ == "__main__":
    main() 
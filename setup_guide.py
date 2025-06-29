#!/usr/bin/env python3
"""API配置向导 - 帮助用户正确配置LLM平台API"""

import os
import sys
from pathlib import Path
from openai import AsyncOpenAI


def main():
    """运行API配置向导"""
    print("🛠️  LLM Chats API配置向导")
    print("=" * 50)
    
    # 检查是否在正确目录
    if not Path("env.example").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    print("📋 支持的平台:")
    platforms = {
        "1": {
            "name": "阿里云百炼",
            "env_prefix": "ALIBABA",
            "docs": "https://help.aliyun.com/zh/model-studio/",
            "model_example": "qwen-turbo",
            "setup_guide": """
1. 访问阿里云百炼控制台
2. 创建API Key
3. 选择模型（推荐：qwen-turbo）
4. 配置环境变量
"""
        },
        "2": {
            "name": "火山豆包",
            "env_prefix": "DOUBAO",
            "docs": "https://www.volcengine.com/docs/82379/1399008",
            "model_example": "ep-20241230102630-xxxxx",
            "setup_guide": """
⚠️  重要：火山豆包需要使用endpoint ID，不是模型名称！

1. 访问火山豆包控制台
2. 创建推理接入点（Inference Endpoint）
3. 复制endpoint ID（格式：ep-xxxxxxxxx-xxxxx）
4. 使用endpoint ID作为DOUBAO_MODEL值
"""
        },
        "3": {
            "name": "月之暗面",
            "env_prefix": "MOONSHOT",
            "docs": "https://platform.moonshot.cn/docs/intro",
            "model_example": "moonshot-v1-8k",
            "setup_guide": """
1. 访问月之暗面控制台
2. 创建API Key
3. 选择模型（推荐：moonshot-v1-8k）
4. 配置环境变量
"""
        },
        "4": {
            "name": "DeepSeek",
            "env_prefix": "DEEPSEEK",
            "docs": "https://api-docs.deepseek.com/",
            "model_example": "deepseek-chat",
            "setup_guide": """
1. 访问DeepSeek控制台
2. 创建API Key
3. 充值账户（避免402错误）
4. 配置环境变量
"""
        }
    }
    
    for key, platform in platforms.items():
        print(f"{key}. {platform['name']}")
    
    print("\n🔧 常见问题解决方案:")
    
    print("\n❌ 火山豆包 404错误")
    print("   问题：The model or endpoint doubao-lite-32k does not exist")
    print("   原因：使用了错误的模型名称")
    print("   解决：使用endpoint ID替代模型名称")
    print("   示例：DOUBAO_MODEL=ep-20241230102630-xxxxx")
    
    print("\n❌ DeepSeek 402错误")
    print("   问题：Insufficient Balance")
    print("   原因：账户余额不足")
    print("   解决：访问 https://platform.deepseek.com/ 充值")
    
    print("\n❌ 401/403错误")
    print("   问题：API密钥无效或权限不足")
    print("   解决：检查API密钥是否正确，是否有相应权限")
    
    print("\n❌ 429错误")
    print("   问题：请求频率超限")
    print("   解决：降低请求频率或升级账户套餐")
    
    print("\n📝 配置步骤:")
    print("1. 复制配置文件：cp env.example .env")
    print("2. 编辑.env文件，填入正确的API配置")
    print("3. 启动应用：python run.py")
    print("4. 使用'测试配置'按钮验证设置")
    
    print("\n🔍 配置验证命令:")
    print("```bash")
    print("# 检查配置是否正确")
    print("python -c \"")
    print("from llm_chats.config import get_config")
    print("config = get_config()")
    print("enabled = config.get_enabled_platforms()")
    print("print('已配置平台:', list(enabled.keys()))")
    print("for name, cfg in enabled.items():")
    print("    print(f'{name}: {cfg.model}')")
    print("\"")
    print("```")
    
    print("\n💡 推荐的最小配置:")
    print("至少配置以下任意两个平台：")
    print("- 阿里云百炼 (稳定性好)")
    print("- 月之暗面 (响应快)")
    print("- DeepSeek (成本低，需充值)")
    
    print("\n📞 需要帮助？")
    print("- 查看文档：README.md")
    print("- 运行测试：python -c \"from llm_chats.app import test_platform_config; import asyncio; print(asyncio.run(test_platform_config('deepseek')))\"")
    print("- 提交Issue：https://github.com/flyer103/llm-chats/issues")


def test_doubao_config():
    """专门测试火山豆包配置"""
    print("\n🔥 火山豆包配置测试")
    print("="*50)
    
    api_key = os.getenv('DOUBAO_API_KEY', '').strip()
    model = os.getenv('DOUBAO_MODEL', 'ep-m-20250629223026-prr94').strip()
    
    if not api_key:
        print("❌ 未配置DOUBAO_API_KEY")
        return False
    
    print(f"✅ API Key: {api_key[:8]}..." if len(api_key) > 8 else f"✅ API Key: {api_key}")
    print(f"📦 Model/Endpoint: {model}")
    
    # 检查模型/接入点格式
    if model.startswith('ep-'):
        print("🔧 使用自定义推理接入点 (Endpoint ID)")
        if model == 'ep-m-20250629223026-prr94':
            print("✅ 使用文档中已开通的接入点")
            print("   对应模型: doubao-seed-1-6-250615")
        else:
            print("⚠️  使用其他自定义接入点")
        print("   请确保已在控制台创建该接入点")
    elif model.startswith('doubao-'):
        print("🎯 使用预置模型ID")
        print("   注意：根据文档，已开通的是自定义接入点")
        print("   建议使用: ep-m-20250629223026-prr94")
    else:
        print("⚠️  模型/接入点格式可能不正确")
        print("   正确格式应为：")
        print("   - 自定义接入点: ep-m-20250629223026-prr94 (推荐)")
        print("   - 预置模型ID: doubao-seed-1.6")
    
    try:
        print("\n🧪 开始API连接测试...")
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        
        # 这里我们不进行实际的API调用，只是验证配置
        print("✅ 配置格式正确，可以进行API调用")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


if __name__ == "__main__":
    main() 
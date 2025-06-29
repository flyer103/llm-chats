#!/usr/bin/env python3
"""
验证火山豆包接入点配置的简单测试脚本
"""

import os
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_doubao_endpoint():
    """测试火山豆包接入点配置"""
    print("🔥 火山豆包接入点配置验证")
    print("="*50)
    
    api_key = os.getenv('DOUBAO_API_KEY', '').strip()
    model = os.getenv('DOUBAO_MODEL', 'ep-m-20250629223026-prr94').strip()
    base_url = os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3').strip()
    
    print(f"🔑 API Key: {'已配置' if api_key else '❌ 未配置'}")
    print(f"🎯 接入点: {model}")
    print(f"🌐 Base URL: {base_url}")
    
    if not api_key:
        print("\n❌ 请先配置DOUBAO_API_KEY")
        return False
    
    # 检查接入点格式
    if model == 'ep-m-20250629223026-prr94':
        print("✅ 使用文档中已开通的正确接入点")
        print("   对应模型ID: doubao-seed-1-6-250615")
    elif model.startswith('ep-'):
        print("⚠️  使用其他自定义接入点，请确保已在控制台创建")
    else:
        print("❌ 接入点格式不正确")
        print("   应该使用: ep-m-20250629223026-prr94")
        return False
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        print("\n🧪 发送测试请求...")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下你自己"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ API调用成功！")
        print(f"📝 模型响应: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        
        # 提供具体的错误分析
        error_str = str(e).lower()
        if '404' in error_str or 'not found' in error_str:
            print("\n🔍 错误分析：接入点不存在或无权限访问")
            print("   请检查：")
            print("   1. 接入点ID是否正确")
            print("   2. 是否已在火山豆包控制台创建该接入点")
            print("   3. API密钥是否有权限访问该接入点")
        elif '401' in error_str or 'unauthorized' in error_str:
            print("\n🔍 错误分析：API密钥无效")
            print("   请检查火山豆包控制台中的API密钥")
        elif '402' in error_str or 'balance' in error_str:
            print("\n🔍 错误分析：账户余额不足")
            print("   请在火山豆包控制台充值")
        
        return False

async def main():
    """主函数"""
    print("🚀 火山豆包接入点配置验证")
    print("="*60)
    
    success = await test_doubao_endpoint()
    
    print("\n📋 测试结果:")
    if success:
        print("✅ 火山豆包配置正确，可以正常使用")
        print("\n🎉 现在可以启动完整系统:")
        print("   python run.py")
    else:
        print("❌ 配置有问题，请检查设置")
        print("\n🔧 建议操作:")
        print("   1. 检查 .env 文件中的配置")
        print("   2. 确认接入点ID: ep-m-20250629223026-prr94")
        print("   3. 验证API密钥是否正确")
        print("   4. 运行配置向导: python setup_guide.py")

if __name__ == '__main__':
    asyncio.run(main()) 
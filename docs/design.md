# 多LLM对话系统设计文档 (2025年6月更新版)

## 1. 项目概述

基于多个大型语言模型平台的对话系统，让不同AI模型就同一话题进行讨论，通过多方对话探索深入理解话题的效果。

## 2. 支持的平台和最新模型列表

### 2.1 阿里云百炼 (Alibaba Cloud Model Studio)
- **平台地址**: https://help.aliyun.com/zh/model-studio/
- **模型列表**: https://help.aliyun.com/zh/model-studio/models
- **控制台**: https://bailian.console.aliyun.com/

#### 推荐模型 (2025年最新):
1. **qwen-max-2024-09-19** (推荐旗舰模型)
   - 最强性能，32K上下文窗口
   - 适合复杂推理和创作任务
   
2. **qwen-plus-2024-09-19** (均衡选择)
   - 性能与成本均衡，32K上下文窗口
   - 适合日常对话和分析任务
   
3. **qwen-turbo-2024-11-01** (高速模型)
   - 响应速度快，128K上下文窗口
   - 适合快速交互场景
   
4. **qwen-long-2024-09-19** (长文本模型)
   - 1M上下文窗口，适合长文档处理
   
5. **qwen2.5-72b-instruct** (开源版本)
   - 开源模型，可本地部署

### 2.2 火山豆包 (Volcano Engine Doubao)
- **平台地址**: https://www.volcengine.com/product/doubao  
- **控制台**: https://console.volcengine.com/ark
- **文档**: https://www.volcengine.com/docs/82379

#### 开通的模型

已接入如下模型，模型 ID 和接入点如下：
- 模型 ID: doubao-seed-1-6-250615
- 接入点: ep-m-20250629223026-prr94

#### 推荐模型 (2025年最新):
1. **doubao-seed-1.6** (🌟 最新旗舰模型，推荐)
   - 多模态深度思考模型，256K上下文
   - 支持文本、图像、视频理解
   - 同时支持thinking、non-thinking、auto三种思考模式
   
2. **doubao-seed-1.6-flash** (高速版本)
   - 极致推理速度，256K上下文
   - 保持高性能的同时提升响应速度
   
3. **doubao-seed-1.6-thinking** (深度思考增强版)
   - 强化思考能力，256K上下文
   - 在编程、数学、逻辑推理等基础能力上进一步提升
   
4. **doubao-1.5-pro-32k** (经典推荐)
   - 32K上下文，综合性能优秀
   - 性价比高，适合生产环境
   
5. **doubao-1.5-lite-32k** (轻量高效)
   - 32K上下文，轻量级模型
   - 成本较低，适合高频调用
   
6. **doubao-1.5-pro-256k** (长文本版本)
   - 256K超长上下文窗口
   
7. **doubao-1.5-vision-pro** (视觉理解模型)
   - 支持图像理解和分析

#### 🔥 重要配置说明

**火山豆包有两种接入方式**：

1. **预置推理接入点**（推荐，即开即用）：
   - 直接使用预置模型ID，如：`doubao-seed-1.6`
   - 无需额外配置，开通即可使用
   - 预置模型ID列表：https://www.volcengine.com/docs/82379/1330310

2. **自定义推理接入点**（高级功能）：
   - 需要在控制台创建推理接入点
   - 获得Endpoint ID（格式：`ep-20241230102630-xxxxx`）
   - 支持精调模型、权限控制、算力保障等功能
   - 创建指南：https://www.volcengine.com/docs/82379/1099522

**配置建议**：
- 初次使用推荐选择预置模型ID：`doubao-seed-1.6`
- 如需特殊功能，可创建自定义推理接入点

#### 常见问题排查

**404错误**：
- 检查模型名称是否正确（区分大小写）
- 确认使用的是预置模型ID而非描述性名称
- 如使用Endpoint ID，确保格式正确且已创建

**推荐配置**：
```bash
DOUBAO_API_KEY=your_api_key_here
DOUBAO_MODEL=doubao-seed-1.6
```

### 2.3 月之暗面 (Moonshot AI)
- **平台地址**: https://kimi.ai/
- **控制台**: https://platform.moonshot.cn/
- **API文档**: https://platform.moonshot.cn/docs

#### 推荐模型 (2025年最新):
1. **moonshot-v1-128k** (推荐使用)
   - 128K超长上下文窗口
   - 支持超长文本处理，最高2M字符输入
   
2. **moonshot-v1-32k** (标准版本)
   - 32K上下文窗口
   - 均衡的性能和成本
   
3. **moonshot-v1-8k** (基础版本)
   - 8K上下文窗口
   - 基础对话和简单任务

**特色功能**: 
- 支持超长文本处理能力
- 专门优化的中文理解
- 强大的文档分析能力

### 2.4 DeepSeek (深度求索)
- **平台地址**: https://www.deepseek.com/
- **控制台**: https://platform.deepseek.com/
- **API文档**: https://api-docs.deepseek.com/

#### 推荐模型 (2025年最新):
1. **deepseek-reasoner** (推荐使用，R1-0528)
   - 最新推理模型，强大的逻辑推理能力
   - 优秀的数学和科学问题解答能力
   - 支持复杂的多步推理
   
2. **deepseek-chat** (对话模型，V3-0324)
   - 685B参数的混合专家模型
   - 均衡的对话和生成能力
   - 64K上下文窗口

**特色功能**:
- R1推理模型具备强大的逻辑推理和数学能力
- 提供峰谷定价，非高峰期有大幅折扣
- 开源友好，部分模型完全开源

## 3. 系统架构

### 3.1 核心组件
- **配置管理** (`config.py`): 统一管理各平台API配置
- **客户端实现** (`client.py`): 各平台统一接口实现
- **对话管理** (`conversation.py`): 多方对话协调和状态管理
- **用户界面** (`app.py`): Gradio Web界面

### 3.2 技术特性
- 异步并发处理
- 统一的OpenAI SDK接口
- 完善的错误处理和重试机制
- 实时进度监控
- 对话历史保存和导出
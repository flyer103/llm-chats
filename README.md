# 🤖 LLM Chats - 多方AI对话系统

## 项目介绍

基于多个大型语言模型平台的对话系统，让不同AI模型就同一话题进行讨论，通过多方对话探索深入理解话题的效果。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-orange.svg)](https://github.com/astral-sh/uv)

## ✨ 特性

- 🔄 **多平台集成**: 支持阿里云百炼、火山豆包、月之暗面、DeepSeek四大主流LLM平台
- 🚀 **异步并发**: 高效的异步处理，支持多模型同时对话
- 🎨 **可视化界面**: 基于Gradio的Web界面，实时显示对话进度
- 📊 **进度监控**: 实时显示对话状态和各模型响应情况
- 💾 **对话存储**: 完整的对话历史记录和导出功能
- 🔧 **灵活配置**: 支持环境变量配置，易于部署和管理
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 🌐 **统一接口**: 使用OpenAI SDK统一各平台调用接口

## 🆕 2025年6月更新亮点

### 最新模型支持

- **阿里云百炼**: qwen-max-2024-09-19, qwen-plus-2024-09-19, qwen-turbo-2024-11-01
- **火山豆包**: Doubao-Seed-1.6, Doubao-1.5-pro-32k, Doubao-1.5-lite-32k
- **月之暗面**: moonshot-v1-128k (超长上下文支持)
- **DeepSeek**: deepseek-reasoner (R1推理模型), deepseek-chat (V3对话模型)

### 新增功能

- 🧠 **推理模型支持**: DeepSeek-R1推理模型，强大的逻辑推理能力
- 👁️ **多模态能力**: 火山豆包视觉理解模型支持
- ⏰ **峰谷定价**: DeepSeek非高峰期75%折扣支持
- 🔍 **智能模型选择**: 根据使用场景的模型推荐

## 📋 支持的平台和模型

### 阿里云百炼 (Alibaba Cloud Model Studio)
- **控制台**: https://bailian.console.aliyun.com/
- **推荐模型**: qwen-max-2024-09-19 (旗舰模型)
- **特色**: 32K-1M上下文，中文优化

### 火山豆包 (Volcano Engine Doubao)
- **控制台**: https://console.volcengine.com/ark
- **推荐模型**: Doubao-1.5-pro-32k (均衡性价比)
- **特色**: 多模态理解，GUI操作能力

### 月之暗面 (Moonshot AI)
- **控制台**: https://platform.moonshot.cn/
- **推荐模型**: moonshot-v1-128k (超长上下文)
- **特色**: 支持2M字符输入，文档分析专长

### DeepSeek (深度求索)
- **控制台**: https://platform.deepseek.com/
- **推荐模型**: deepseek-reasoner (推理模型)
- **特色**: 强逻辑推理，峰谷定价优惠

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装UV包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/your-username/llm-chats.git
cd llm-chats

# 安装依赖
uv sync
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env文件，填入您的API密钥
```

**环境变量配置示例**：
```bash
# 至少配置一个平台的API密钥
ALIBABA_API_KEY=your_alibaba_api_key_here
DOUBAO_API_KEY=your_doubao_api_key_here  
MOONSHOT_API_KEY=your_moonshot_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 模型选择 (可选，使用推荐模型)
ALIBABA_MODEL=qwen-max-2024-09-19
DOUBAO_MODEL=Doubao-1.5-pro-32k
MOONSHOT_MODEL=moonshot-v1-128k
DEEPSEEK_MODEL=deepseek-reasoner
```

### 3. 运行应用

```bash
# 方式1: 智能启动 (推荐)
python run.py

# 方式2: UV包管理器启动
uv run llm-chats

# 方式3: 简单启动
python main.py
```

### 4. 配置验证

```bash
# 验证配置是否正确
python -c "from llm_chats.config import get_config; config = get_config(); enabled = config.get_enabled_platforms(); print('已配置平台:', list(enabled.keys()))"
```

## 🎯 使用场景推荐

### 按场景选择模型

**复杂推理和数学问题**:
1. DeepSeek-reasoner (首选)
2. Doubao-Seed-1.6
3. qwen-max-2024-09-19

**日常对话和创作**:
1. qwen-plus-2024-09-19
2. Doubao-1.5-pro-32k
3. moonshot-v1-32k

**长文档处理**:
1. moonshot-v1-128k (首选)
2. qwen-long-2024-09-19
3. Doubao-1.5-pro-256k

**快速响应场景**:
1. qwen-turbo-2024-11-01
2. Doubao-Seed-1.6-flash
3. Doubao-1.5-lite-32k

**成本敏感场景**:
1. Doubao-1.5-lite-32k
2. DeepSeek-chat (非高峰期)
3. moonshot-v1-8k

## 🛠️ 技术架构

### 核心组件

- **配置管理** (`config.py`): 统一环境变量和模型配置
- **客户端层** (`client.py`): 各平台统一OpenAI SDK接口
- **对话管理** (`conversation.py`): 多方对话协调和状态管理
- **用户界面** (`app.py`): Gradio Web界面和交互逻辑

### 技术栈

- **Python 3.12+**: 核心开发语言
- **UV**: 现代Python包管理器
- **OpenAI SDK**: 统一的API调用接口
- **Gradio**: Web界面框架
- **Asyncio**: 异步并发处理
- **Pydantic**: 数据验证和类型安全

## 📊 项目结构

```
llm-chats/
├── src/llm_chats/          # 核心代码模块
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── client.py           # LLM客户端实现
│   ├── conversation.py     # 对话管理
│   └── app.py              # Gradio应用
├── docs/                   # 文档目录
│   └── 2025.06.29.md       # 设计文档
├── conversations/          # 对话历史 (自动创建)
├── run.py                  # 智能启动脚本
├── main.py                 # 简单启动
├── env.example             # 环境变量模板
├── pyproject.toml          # UV项目配置
├── README.md               # 项目说明
└── LICENSE                 # Apache 2.0许可证
```

## 🔧 高级配置

### 对话参数调整

```bash
# 对话轮数限制
MAX_CONVERSATION_ROUNDS=5

# 单次响应超时时间 (秒)
RESPONSE_TIMEOUT=30

# 温度参数 (0.0-2.0)
DEFAULT_TEMPERATURE=0.7

# 最大输出tokens
DEFAULT_MAX_TOKENS=1000
```

### Gradio界面配置

```bash
# 界面端口
GRADIO_PORT=7860

# 外部访问
GRADIO_SHARE=false

# 界面标题
GRADIO_TITLE=多LLM对话系统
```

## ❗ 故障排除

### 常见问题

1. **API密钥错误**: 检查`.env`文件中的API密钥是否正确
2. **模型不存在**: 使用本文档推荐的最新模型名称
3. **火山豆包404错误**: 确保使用endpoint ID而非模型名称
4. **网络连接问题**: 检查网络和防火墙设置
5. **配额不足**: 检查各平台账户余额

### 调试方法

```bash
# 启用调试日志
LOG_LEVEL=DEBUG

# 检查环境变量
python -c "from llm_chats.config import get_config; print(get_config())"
```

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。
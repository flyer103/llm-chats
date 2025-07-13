# 🤖 LLM Chats - 多方AI对话系统

## 项目介绍

基于多个大型语言模型平台的对话系统，让不同AI模型就同一话题进行讨论，通过多方对话探索深入理解话题的效果。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-orange.svg)](https://github.com/astral-sh/uv)

## ✨ 特性

- 🔄 **多平台集成**: 支持阿里云百炼、火山豆包、月之暗面、DeepSeek、Ollama五大主流LLM平台
- 🚀 **异步并发**: 高效的异步处理，支持多模型同时对话
- 🎨 **可视化界面**: 基于Gradio的Web界面，实时显示对话进度
- 📊 **进度监控**: 实时显示对话状态和各模型响应情况
- 💾 **对话存储**: 完整的对话历史记录和导出功能
- 🔧 **灵活配置**: 支持环境变量配置，易于部署和管理
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 🌐 **统一接口**: 使用OpenAI SDK统一各平台调用接口
- 📎 **文件上传**: 支持PDF、图片等文件上传，智能提取内容作为对话上下文
- 🤖 **智能模型更新**: 联网自动获取各平台最新模型配置
- 📝 **对话总结**: AI生成高质量深度研究文章，支持多种风格和格式
- 🎯 **自由选择**: 用户可选择任意模型进行对话总结

## 🆕 2025年7月更新亮点

### 最新模型支持 (自动更新)

- **阿里云百炼**: qwen-max-2024-09-19, qwen-plus-2024-09-19, qwen-turbo-2024-11-01
- **火山豆包**: doubao-pro-128k-v1.5, doubao-pro-32k-v1.5, doubao-pro-4k-v1.5  
- **月之暗面**: moonshot-v1-128k, moonshot-v1-32k, moonshot-v1-8k
- **DeepSeek**: deepseek-reasoner (R1推理模型), deepseek-chat, deepseek-coder
- **Ollama**: deepseek-r1:8b, llama3.2:latest, qwen2.5:latest (本地模型)

### 新增核心功能

- 🤖 **智能模型更新**: 一键联网获取各平台最新模型配置，自动更新 .env.example
- 📝 **AI深度总结**: 对话结束后生成高质量深度研究文章，支持学术、博客、报告三种风格
- 🎯 **灵活模型选择**: 用户可自由选择任意模型进行对话总结，满足不同需求
- 📄 **多格式导出**: 支持 Markdown、HTML、JSON 三种格式导出总结
- 📊 **智能统计**: 自动生成对话统计信息，包含参与度分析和时间分布

## 📋 支持的平台和模型

### 阿里云百炼 (Alibaba Cloud Model Studio)
- **控制台**: https://bailian.console.aliyun.com/
- **推荐模型**: qwen-max-2024-09-19 (旗舰模型，32K上下文)
- **其他选项**: qwen-plus-2024-09-19 (均衡性价比), qwen-turbo-2024-11-01 (快速响应，128K上下文)
- **特色**: 中文优化，适合复杂推理任务

### 火山豆包 (Volcano Engine Doubao)
- **控制台**: https://console.volcengine.com/ark
- **推荐模型**: doubao-pro-128k-v1.5 (超长上下文，128K)
- **其他选项**: doubao-pro-32k-v1.5 (标准版), doubao-pro-4k-v1.5 (对话专用)
- **特色**: 128K上下文，支持文档分析

### 月之暗面 (Moonshot AI)
- **控制台**: https://platform.moonshot.cn/
- **推荐模型**: moonshot-v1-128k (超长上下文，128K)
- **其他选项**: moonshot-v1-32k (标准版), moonshot-v1-8k (基础版)
- **特色**: 支持2M字符输入，文档分析专长

### DeepSeek (深度求索)
- **控制台**: https://platform.deepseek.com/
- **推荐模型**: deepseek-reasoner (R1推理模型，强逻辑推理)
- **其他选项**: deepseek-chat (对话模型), deepseek-coder (编程专用)
- **特色**: 强逻辑推理能力，峰谷定价优惠

### Ollama (本地模型)
- **官网**: https://ollama.com/
- **推荐模型**: deepseek-r1:8b (本地推理模型，强逻辑推理)
- **其他选项**: llama3.2:latest (通用对话), qwen2.5:latest (中文支持)
- **特色**: 本地部署，数据隐私保护，无需网络

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装UV包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/your-username/llm-chats.git
cd llm-chats

# 安装依赖 (包括新增的文件处理依赖)
uv sync

# 安装额外的系统依赖 (用于OCR功能)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim libmagic1
# macOS:
brew install tesseract tesseract-lang libmagic
# Windows: 请参考 https://github.com/UB-Mannheim/tesseract/wiki
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

# 模型选择 (可选，系统会自动使用最新推荐模型)
ALIBABA_MODEL=qwen-max-2024-09-19
DOUBAO_MODEL=ep-pro-128k-v1-5  # 使用endpoint ID格式
MOONSHOT_MODEL=moonshot-v1-128k
DEEPSEEK_MODEL=deepseek-reasoner

# Ollama本地模型 (可选)
OLLAMA_ENABLED=true
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_BASE_URL=http://localhost:11434/
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

## 🎨 主要功能使用

### 多方对话功能
1. **启动应用**后，在Web界面左侧配置讨论话题
2. **选择参与平台**：可选择多个AI模型参与对话
3. **设置参数**：配置最大轮次和超时时间
4. **开始讨论**：点击"开始讨论"按钮启动多方对话

### 📝 AI深度总结功能（新增）
1. **完成对话**后，在界面右侧找到"对话总结"区域
2. **选择总结模型**：从下拉框中选择用于生成总结的AI模型
3. **配置总结参数**：
   - **文章风格**：学术研究、博客文章、研究报告
   - **输出格式**：Markdown、HTML、JSON
   - **最大字数**：1000-10000字可调
   - **包含统计**：是否包含对话统计信息
4. **生成总结**：点击"生成总结"按钮，AI将自动生成深度研究文章
5. **导出总结**：生成完成后点击"导出总结"保存为文件

### 🤖 智能模型更新功能（新增）
1. **点击"更新模型"按钮**：系统会联网获取各平台最新模型信息
2. **自动更新配置**：系统会自动更新 .env.example 文件中的模型配置
3. **查看更新报告**：系统会生成详细的模型对比报告

### 📎 文件上传功能
1. **上传文件**：支持PDF、图片等格式
2. **自动处理**：系统会智能提取文件内容
3. **作为上下文**：文件内容会自动加入对话上下文

## 🎯 使用场景推荐

### 按场景选择模型

**复杂推理和数学问题**:
1. deepseek-reasoner (R1推理模型，首选)
2. deepseek-r1:8b (本地推理，隐私保护)
3. qwen-max-2024-09-19 (旗舰模型)

**对话总结和文章生成**:
1. qwen-max-2024-09-19 (综合能力强)
2. deepseek-reasoner (逻辑清晰)
3. moonshot-v1-128k (长文本理解)

**长文档分析**:
1. moonshot-v1-128k (128K上下文，首选)
2. doubao-pro-128k-v1.5 (128K上下文)
3. qwen-turbo-2024-11-01 (128K上下文，快速)

**日常对话和创作**:
1. qwen-plus-2024-09-19 (均衡性价比)
2. deepseek-chat (对话专用)
3. moonshot-v1-32k (标准版)

**快速响应场景**:
1. qwen-turbo-2024-11-01 (快速响应)
2. doubao-pro-4k-v1.5 (对话专用)
3. moonshot-v1-8k (基础版)

**成本敏感场景**:
1. deepseek-r1:8b (本地免费)
2. llama3.2:latest (本地免费)
3. deepseek-chat (非高峰期75折)

**编程和代码分析**:
1. deepseek-coder (编程专用)
2. qwen-max-2024-09-19 (全能)
3. deepseek-r1:8b (本地编程)

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
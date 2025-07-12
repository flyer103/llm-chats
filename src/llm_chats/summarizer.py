"""Conversation summarizer for generating deep research articles."""
import asyncio
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import re

from .client import BaseLLMClient, Message, ChatResponse
from .conversation import Conversation, ConversationRound

logger = logging.getLogger(__name__)


@dataclass
class SummaryConfig:
    """Configuration for conversation summary."""
    output_format: str = "markdown"  # markdown, html, json
    include_metadata: bool = True
    include_statistics: bool = True
    language: str = "zh"  # zh, en
    article_style: str = "academic"  # academic, blog, report
    
    def get_style_prompt(self) -> str:
        """Get style-specific prompt."""
        if self.article_style == "academic":
            return """
请以深度学术研究的风格撰写，包含：
1. **研究背景与问题陈述**: 深入分析讨论主题的学术背景和核心问题
2. **理论框架与方法论**: 梳理讨论中涉及的理论基础和分析方法
3. **核心观点综合分析**: 系统整理各参与者的主要观点，并进行批判性分析
4. **创新洞察与原创观点**: 基于讨论内容提出自己的独到见解和理论贡献
5. **实践应用与发展前景**: 分析理论在实践中的应用价值和未来发展方向
6. **可视化支持**: 使用表格对比不同观点，用流程图展示逻辑关系
7. **完整参考文献**: 整合所有讨论中的参考资料，建立权威文献库

确保内容深度与广度并重，字数不限，充分展开论述。
"""
        elif self.article_style == "blog":
            return """
请以适合微信公众号发表的深度博客文章风格撰写，要求直接可发表，无需任何修改：

## 📝 微信公众号文章标准
1. **吸睛标题与开头**: 
   - 设计引人入胜的标题（包含数字、疑问或热点词汇）
   - 开篇用热门话题、惊人数据或引人思考的问题抓住读者注意力
   - 快速建立与读者的共鸣和代入感

2. **结构化内容布局**:
   - 使用大量小标题、分点列举、emoji表情增强可读性
   - 每个段落控制在3-5句话，适合手机阅读
   - 合理使用**加粗**、*斜体*突出重点内容

3. **互动性设计**:
   - 在文中设置引导性问题："你是否也遇到过这样的问题？"
   - 使用"我们来看看..."、"不妨想想..."等互动表达
   - 结尾设置讨论话题，鼓励读者留言互动

4. **视觉化增强**:
   - 大量使用表格对比、流程图、思维导图
   - 用📊📈📉等emoji和符号增强视觉效果
   - 通过引用框突出核心观点和金句

5. **价值输出导向**:
   - 提供立即可用的实操建议和行动清单
   - 分享独家见解和前瞻性判断
   - 给出明确的"干货"总结和要点梳理

6. **情感连接**:
   - 使用贴近生活的案例和比喻
   - 适当融入热点事件和网络流行语
   - 保持温度感，避免过于学术化的表达

7. **完整文章结构**:
   - 标题（含副标题）
   - 引言/开头钩子
   - 主体内容（3-5个核心部分）
   - 总结要点
   - 行动建议
   - 互动引导结尾

## 🎯 发表标准要求
- 内容完整，可直接复制粘贴发表
- 语言生动，符合社交媒体传播特点
- 观点独到，具有分享价值和讨论性
- 排版优美，适合手机端阅读体验
- 包含明确的读者获得感和行动指引

请确保生成的文章达到微信公众号10W+爆款文章的质量标准，读者看完就想转发分享！
"""
        elif self.article_style == "report":
            return """
请以专业研究报告的风格撰写，包含：
1. **执行摘要**: 核心发现和主要结论的高度概括
2. **问题分析**: 深入分析讨论主题涉及的关键问题和挑战
3. **方案对比**: 系统比较讨论中提出的不同解决方案
4. **数据支撑**: 整理和分析讨论中的关键数据和案例
5. **风险评估**: 识别和分析各种方案的潜在风险和局限性
6. **图表分析**: 使用表格、流程图等可视化工具辅助分析
7. **创新建议**: 基于分析结果提出具有创新性的实施建议和行动方案

注重逻辑性和实用性，字数不限，确保分析全面深入。
"""
        else:
            return """
请以专业、深入的风格撰写文章，要求：
- 字数不限，确保内容完整全面
- 整理讨论精华，形成原创观点
- 使用图表增强理解效果
- 提供具有实践价值的洞察
"""


@dataclass
class SummaryResult:
    """Summary generation result."""
    content: str
    metadata: Dict[str, Any]
    statistics: Dict[str, Any]
    generated_at: str
    generated_by: str
    config: SummaryConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "statistics": self.statistics,
            "generated_at": self.generated_at,
            "generated_by": self.generated_by,
            "config": {
                "output_format": self.config.output_format,
                "article_style": self.config.article_style,
                "language": self.config.language
            }
        }


class ConversationSummarizer:
    """Generate deep research articles from conversations."""
    
    def __init__(self, clients: Dict[str, BaseLLMClient]):
        self.clients = clients
    
    def get_available_models(self) -> List[str]:
        """Get list of available models for summarization."""
        return list(self.clients.keys())
    
    async def generate_summary(self, conversation: Conversation, 
                             model_name: str, 
                             config: SummaryConfig) -> SummaryResult:
        """Generate a comprehensive summary of the conversation."""
        logger.info(f"Generating summary using {model_name}")
        
        if model_name not in self.clients:
            raise ValueError(f"Model {model_name} not available")
        
        client = self.clients[model_name]
        
        # Extract conversation content
        messages = conversation.get_all_messages()
        
        # Generate statistics
        statistics = self._generate_statistics(conversation, messages)
        
        # Generate metadata
        metadata = self._generate_metadata(conversation)
        
        # Create summary prompt
        summary_prompt = self._create_summary_prompt(
            conversation, messages, config, statistics
        )
        
        # Generate summary with enhanced max_tokens for comprehensive output
        try:
            # Create a temporary client configuration with higher max_tokens for summary generation
            original_max_tokens = client.config.max_tokens
            
            # Set max_tokens based on article style and model capabilities
            if config.article_style == "academic":
                # Academic articles need more detailed analysis
                client.config.max_tokens = 8000
            elif config.article_style == "blog":
                # Blog articles for social media need comprehensive content
                client.config.max_tokens = 6000
            elif config.article_style == "report":
                # Research reports need extensive analysis
                client.config.max_tokens = 7000
            else:
                # Default comprehensive output
                client.config.max_tokens = 5000
            
            # Adjust max_tokens based on model capabilities
            model_lower = client.config.model.lower()
            if "gpt-4" in model_lower or "claude" in model_lower:
                # High-capability models can handle more tokens
                client.config.max_tokens = min(client.config.max_tokens, 8000)
            elif "gpt-3.5" in model_lower:
                # Standard models
                client.config.max_tokens = min(client.config.max_tokens, 4000)
            elif "deepseek" in model_lower:
                # DeepSeek models handle long generation well
                client.config.max_tokens = min(client.config.max_tokens, 8000)
            elif "qwen" in model_lower or "alibaba" in model_lower:
                # Qwen models are good at long text generation
                client.config.max_tokens = min(client.config.max_tokens, 6000)
            elif "moonshot" in model_lower:
                # Moonshot models support long context
                client.config.max_tokens = min(client.config.max_tokens, 8000)
            elif "doubao" in model_lower:
                # Doubao models 
                client.config.max_tokens = min(client.config.max_tokens, 6000)
            elif "ollama" in model_lower:
                # Local models may have different constraints
                client.config.max_tokens = min(client.config.max_tokens, 4000)
            
            logger.info(f"Using max_tokens={client.config.max_tokens} for summary generation with {model_name}")
            
            summary_messages = [
                Message(
                    role="user",
                    content=summary_prompt,
                    timestamp=time.time()
                )
            ]
            
            response = await client.chat(summary_messages)
            
            # Restore original max_tokens
            client.config.max_tokens = original_max_tokens
            
            # Post-process the summary
            processed_content = self._post_process_summary(
                response.content, config, metadata, statistics
            )
            
            return SummaryResult(
                content=processed_content,
                metadata=metadata,
                statistics=statistics,
                generated_at=datetime.now().isoformat(),
                generated_by=model_name,
                config=config
            )
            
        except Exception as e:
            # Restore original max_tokens in case of error
            client.config.max_tokens = original_max_tokens
            logger.error(f"Failed to generate summary: {e}")
            raise
    
    def _create_summary_prompt(self, conversation: Conversation, 
                              messages: List[Message], 
                              config: SummaryConfig,
                              statistics: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for summary generation."""
        
        # Extract conversation content
        conversation_content = self._format_conversation_content(messages)
        
        # Base prompt
        base_prompt = f"""
你是一位资深学者和专业作家，负责基于多AI专家的深度讨论内容，撰写一篇具有原创性见解的高质量研究文章。

## 讨论主题
{conversation.config.topic}

## 讨论概况
- 参与专家：{', '.join(conversation.participants)}
- 讨论轮次：{len(conversation.rounds)}轮深度对话
- 总观点数：{statistics.get('total_messages', 0)}个专业见解
- 内容总字数：{statistics.get('total_words', 0)}字的深度分析

## 专家讨论内容
{conversation_content}

## 深度总结要求
{config.get_style_prompt()}

## 输出规范
- 格式：{config.output_format}
- 风格：{config.article_style}
- 语言：{"中文" if config.language == "zh" else "英文"}
- 字数要求：无限制，确保内容完整深入

## 核心任务
1. **观点提炼**: 从讨论中提炼出最有价值的核心观点和深层洞察
2. **综合分析**: 整合不同专家的视角，识别共识点和分歧点
3. **原创贡献**: 基于讨论内容形成自己独特的理论观点和实践建议
4. **逻辑构建**: 建立清晰的论证体系，确保观点之间的逻辑关联性
5. **视觉增强**: 创建表格对比不同观点，用图表展示关键关系和流程
6. **深度思考**: 超越表面总结，提供具有前瞻性的分析和预判
7. **实用价值**: 确保总结内容对读者具有实际指导意义

## 学术标准
- **参考整合**: 系统整理讨论中的所有参考文献，验证观点可信度
- **批判分析**: 对冲突观点进行客观分析，提出调解或选择建议
- **创新视角**: 提出讨论中未充分探讨的新角度或解决方案
- **文献支撑**: 在文章末尾提供完整的参考文献清单
- **质量保证**: 确保内容达到可发表的学术或专业标准

请以学者的严谨态度和作家的优美文笔，创作一篇既有学术深度又具备实用价值的原创性研究文章：
"""
        
        return base_prompt.strip()
    
    def _format_conversation_content(self, messages: List[Message]) -> str:
        """Format conversation content for summary generation."""
        formatted_content = []
        
        current_round = 0
        round_messages = []
        
        for message in messages:
            if message.role == "system":
                continue
                
            if message.role == "user" and round_messages:
                # New round started
                if round_messages:
                    formatted_content.append(self._format_round(current_round, round_messages))
                    round_messages = []
                current_round += 1
            
            round_messages.append(message)
        
        # Add last round
        if round_messages:
            formatted_content.append(self._format_round(current_round, round_messages))
        
        return "\n\n".join(formatted_content)
    
    def _format_round(self, round_num: int, messages: List[Message]) -> str:
        """Format a single round of conversation with reference links."""
        if not messages:
            return ""
        
        # Find the user message (topic/question)
        user_message = None
        assistant_messages = []
        
        for msg in messages:
            if msg.role == "user":
                user_message = msg
            elif msg.role == "assistant":
                assistant_messages.append(msg)
        
        round_content = [f"### 第{round_num}轮讨论"]
        
        if user_message:
            round_content.append(f"**讨论话题**: {user_message.content}")
        
        round_content.append("**各方观点**:")
        
        for msg in assistant_messages:
            platform = msg.platform or "未知平台"
            round_content.append(f"- **{platform}**: {msg.content}")
            
            # Add reference links if available
            if msg.has_references():
                round_content.append(f"  **参考链接**:")
                for ref in msg.references or []:
                    title = ref.get('title', '未知标题')
                    url = ref.get('url', '#')
                    description = ref.get('description', '')
                    
                    if description:
                        round_content.append(f"  - [{title}]({url}): {description}")
                    else:
                        round_content.append(f"  - [{title}]({url})")
        
        return "\n".join(round_content)
    
    def _generate_statistics(self, conversation: Conversation, 
                           messages: List[Message]) -> Dict[str, Any]:
        """Generate conversation statistics."""
        stats = {
            "total_messages": len(messages),
            "total_rounds": len(conversation.rounds),
            "participants": len(conversation.participants),
            "participant_names": conversation.participants,
            "total_words": sum(len(msg.content.split()) for msg in messages if msg.role != "system"),
            "average_words_per_message": 0,
            "conversation_duration": 0,
            "platform_message_counts": {},
            "platform_word_counts": {}
        }
        
        # Calculate average words per message
        user_assistant_messages = [msg for msg in messages if msg.role in ["user", "assistant"]]
        if user_assistant_messages:
            stats["average_words_per_message"] = stats["total_words"] / len(user_assistant_messages)
        
        # Calculate conversation duration
        if conversation.rounds:
            first_round = conversation.rounds[0]
            last_round = conversation.rounds[-1]
            if first_round.start_time and last_round.end_time:
                stats["conversation_duration"] = last_round.end_time - first_round.start_time
        
        # Count messages and words per platform
        for msg in messages:
            if msg.role == "assistant" and msg.platform:
                platform = msg.platform
                stats["platform_message_counts"][platform] = stats["platform_message_counts"].get(platform, 0) + 1
                stats["platform_word_counts"][platform] = stats["platform_word_counts"].get(platform, 0) + len(msg.content.split())
        
        return stats
    
    def _generate_metadata(self, conversation: Conversation) -> Dict[str, Any]:
        """Generate conversation metadata."""
        return {
            "conversation_id": conversation.id,
            "topic": conversation.config.topic,
            "participants": conversation.participants,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "state": conversation.state.value,
            "config": {
                "max_rounds": conversation.config.max_rounds,
                "round_timeout": conversation.config.round_timeout,
                "max_participants": conversation.config.max_participants
            }
        }
    
    def _post_process_summary(self, content: str, 
                            config: SummaryConfig,
                            metadata: Dict[str, Any],
                            statistics: Dict[str, Any]) -> str:
        """Post-process the generated summary."""
        processed_content = content
        
        # Add metadata header if requested
        if config.include_metadata:
            header = self._generate_metadata_header(metadata, statistics, config)
            processed_content = header + "\n\n" + processed_content
        
        # Extract and validate reference links
        processed_content = self._process_reference_links(processed_content)
        
        # Add statistics footer if requested
        if config.include_statistics:
            footer = self._generate_statistics_footer(statistics, config)
            processed_content = processed_content + "\n\n" + footer
        
        # Format based on output format
        if config.output_format == "html":
            processed_content = self._convert_to_html(processed_content)
        elif config.output_format == "json":
            processed_content = self._convert_to_json(processed_content, metadata, statistics)
        
        return processed_content
    
    def _generate_metadata_header(self, metadata: Dict[str, Any], 
                                statistics: Dict[str, Any],
                                config: SummaryConfig) -> str:
        """Generate metadata header."""
        if config.output_format == "markdown":
            return f"""---
title: "{metadata['topic']}"
conversation_id: {metadata['conversation_id']}
participants: {', '.join(metadata['participants'])}
total_rounds: {statistics['total_rounds']}
total_messages: {statistics['total_messages']}
total_words: {statistics['total_words']}
generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
article_style: {config.article_style}
---"""
        else:
            return f"""# 文章信息
- 讨论主题: {metadata['topic']}
- 参与者: {', '.join(metadata['participants'])}
- 总轮次: {statistics['total_rounds']}
- 总消息数: {statistics['total_messages']}
- 总字数: {statistics['total_words']}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def _generate_statistics_footer(self, statistics: Dict[str, Any], 
                                  config: SummaryConfig) -> str:
        """Generate statistics footer."""
        if config.output_format == "markdown":
            footer = ["## 讨论统计"]
            
            footer.append(f"- **总轮次**: {statistics['total_rounds']}")
            footer.append(f"- **总消息数**: {statistics['total_messages']}")
            footer.append(f"- **总字数**: {statistics['total_words']}")
            footer.append(f"- **平均每条消息字数**: {statistics['average_words_per_message']:.1f}")
            
            if statistics['conversation_duration'] > 0:
                duration_min = statistics['conversation_duration'] / 60
                footer.append(f"- **对话时长**: {duration_min:.1f} 分钟")
            
            if statistics['platform_message_counts']:
                footer.append("\n### 各平台参与情况")
                for platform, count in statistics['platform_message_counts'].items():
                    word_count = statistics['platform_word_counts'].get(platform, 0)
                    footer.append(f"- **{platform}**: {count} 条消息，{word_count} 字")
            
            return "\n".join(footer)
        else:
            return f"统计信息: {json.dumps(statistics, ensure_ascii=False, indent=2)}"
    
    def _convert_to_html(self, content: str) -> str:
        """Convert markdown content to HTML."""
        # Basic markdown to HTML conversion
        html_content = content
        
        # Headers
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        
        # Bold and italic
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
        
        # Lists
        html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html_content, flags=re.DOTALL)
        
        # Paragraphs
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            if p.strip() and not p.startswith('<'):
                html_paragraphs.append(f'<p>{p}</p>')
            else:
                html_paragraphs.append(p)
        
        return '\n\n'.join(html_paragraphs)
    
    def _convert_to_json(self, content: str, metadata: Dict[str, Any], 
                        statistics: Dict[str, Any]) -> str:
        """Convert content to JSON format."""
        json_data = {
            "content": content,
            "metadata": metadata,
            "statistics": statistics,
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(json_data, ensure_ascii=False, indent=2)
    
    def export_summary(self, summary_result: SummaryResult, 
                      filename: Optional[str] = None) -> str:
        """Export summary to file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            topic_safe = re.sub(r'[^\w\s-]', '', summary_result.metadata['topic'])
            topic_safe = re.sub(r'[-\s]+', '-', topic_safe)
            filename = f"summary_{topic_safe}_{timestamp}.{summary_result.config.output_format}"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(summary_result.content)
            logger.info(f"Summary exported to {filename}")
            return f"✅ 总结已导出到 {filename}"
        except Exception as e:
            logger.error(f"Failed to export summary: {e}")
            return f"❌ 导出失败: {e}"
    
    def _process_reference_links(self, content: str) -> str:
        """Process and validate reference links in the content."""
        import re
        
        # Find all markdown links in the content
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        if not links:
            return content
        
        # Extract unique links
        unique_links = {}
        for title, url in links:
            if url not in unique_links:
                unique_links[url] = title
        
        # Add a reference section if there are many links
        if len(unique_links) > 5:
            reference_section = "\n\n## 参考文献\n\n"
            for i, (url, title) in enumerate(unique_links.items(), 1):
                reference_section += f"{i}. [{title}]({url})\n"
            
            content += reference_section
        
        return content 
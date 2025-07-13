"""Model updater for fetching latest models from different LLM platforms."""
import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model information."""
    name: str
    description: str
    context_length: Optional[int] = None
    release_date: Optional[str] = None
    capabilities: Optional[List[str]] = None
    priority: int = 0  # Higher priority means more recent/important
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class PlatformModels:
    """Platform models information."""
    platform: str
    models: List[ModelInfo]
    updated_at: str
    source_url: str
    
    def get_top_models(self, count: int = 3) -> List[ModelInfo]:
        """Get top N models sorted by priority and context length."""
        sorted_models = sorted(self.models, key=lambda x: (x.priority, x.context_length or 0), reverse=True)
        return sorted_models[:count]


class ModelUpdater:
    """Update model information for different platforms."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
    
    def get_alibaba_models(self) -> PlatformModels:
        """Get latest Alibaba Cloud models using multiple sources."""
        logger.info("Fetching Alibaba Cloud models from multiple sources...")
        
        models = []
        source_urls = [
            "https://help.aliyun.com/zh/model-studio/getting-started/models",
            "https://help.aliyun.com/zh/model-studio/developer-reference/api-details"
        ]
        
        # Try API documentation first
        try:
            response = self.session.get(source_urls[0], timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            # Extract qwen models with improved pattern matching
            qwen_patterns = [
                r'(qwen-max-\d{4}-\d{2}-\d{2})',
                r'(qwen-plus-\d{4}-\d{2}-\d{2})',
                r'(qwen-turbo-\d{4}-\d{2}-\d{2})',
                r'(qwen2\.5-\d+b-instruct)',
                r'(qwen2-\d+b-instruct)'
            ]
            
            for pattern in qwen_patterns:
                matches = re.findall(pattern, text_content.lower())
                for model_name in set(matches):
                    priority = 10
                    context_length = 32768
                    description = "通义千问模型"
                    
                    # Determine model type and priority
                    if 'max' in model_name:
                        priority = 15
                        description = "通义千问最强旗舰模型"
                        context_length = 32768
                    elif 'plus' in model_name:
                        priority = 12
                        description = "通义千问均衡性能模型"
                        context_length = 32768
                    elif 'turbo' in model_name:
                        priority = 10
                        description = "通义千问高速模型"
                        context_length = 131072
                    
                    # Extract date for priority
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', model_name)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            # More recent models get higher priority
                            days_since_2024 = (date_obj - datetime(2024, 1, 1)).days
                            priority += days_since_2024 // 30  # Add 1 priority per month
                        except ValueError:
                            pass
                    
                    models.append(ModelInfo(
                        name=model_name,
                        description=f"{description} - {model_name}",
                        context_length=context_length,
                        priority=priority,
                        capabilities=["text-generation", "reasoning", "chinese"]
                    ))
        
        except Exception as e:
            logger.error(f"Failed to scrape Alibaba models: {e}")
        
        # Add known recent models if nothing found
        if not models:
            models = [
                ModelInfo(
                    name="qwen-max-2024-09-19",
                    description="通义千问最强旗舰模型，32K上下文",
                    context_length=32768,
                    priority=15,
                    capabilities=["text-generation", "reasoning", "coding"]
                ),
                ModelInfo(
                    name="qwen-plus-2024-09-19",
                    description="通义千问均衡性能模型，32K上下文",
                    context_length=32768,
                    priority=12,
                    capabilities=["text-generation", "reasoning"]
                ),
                ModelInfo(
                    name="qwen-turbo-2024-11-01",
                    description="通义千问高速模型，128K上下文",
                    context_length=131072,
                    priority=10,
                    capabilities=["text-generation", "fast-response"]
                )
            ]
        
        return PlatformModels(
            platform="阿里云百炼",
            models=models,
            updated_at=datetime.now().isoformat(),
            source_url=source_urls[0]
        )
    
    def get_doubao_models(self) -> PlatformModels:
        """Get latest Doubao models from Volcengine documentation."""
        logger.info("Fetching Doubao models from Volcengine documentation...")
        
        models = []
        source_urls = [
            "https://www.volcengine.com/docs/82379/1099475",
            "https://www.volcengine.com/docs/82379/1263482"
        ]
        
        for source_url in source_urls:
            try:
                response = self.session.get(source_url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                
                # Extract doubao models with improved patterns
                doubao_patterns = [
                    r'(doubao-pro-\d+k-v[\d\.]+)',
                    r'(doubao-lite-\d+k-v[\d\.]+)',
                    r'(doubao-seed-[\d\-]+)',
                    r'(ep-[a-zA-Z0-9\-]+)'
                ]
                
                for pattern in doubao_patterns:
                    matches = re.findall(pattern, text_content.lower())
                    for model_name in set(matches):
                        priority = 10
                        context_length = 4096
                        description = "豆包模型"
                        
                        # Determine model specs
                        if 'pro' in model_name:
                            priority = 15
                            description = "豆包专业版模型"
                        elif 'lite' in model_name:
                            priority = 8
                            description = "豆包轻量版模型"
                        elif 'seed' in model_name:
                            priority = 12
                            description = "豆包种子模型"
                        
                        # Extract context length
                        if '4k' in model_name:
                            context_length = 4096
                        elif '32k' in model_name:
                            context_length = 32768
                        elif '128k' in model_name:
                            context_length = 131072
                        
                        models.append(ModelInfo(
                            name=model_name,
                            description=f"{description} - {model_name}",
                            context_length=context_length,
                            priority=priority,
                            capabilities=["text-generation", "conversation", "chinese"]
                        ))
                
                if models:
                    break  # Found models, no need to try other URLs
                    
            except Exception as e:
                logger.error(f"Failed to scrape Doubao models from {source_url}: {e}")
        
        # Add known recent models if nothing found
        if not models:
            models = [
                ModelInfo(
                    name="doubao-pro-32k-v1.5",
                    description="豆包专业版长文本模型，32K上下文",
                    context_length=32768,
                    priority=15,
                    capabilities=["text-generation", "long-context"]
                ),
                ModelInfo(
                    name="doubao-pro-4k-v1.5",
                    description="豆包专业版模型，4K上下文",
                    context_length=4096,
                    priority=12,
                    capabilities=["text-generation", "conversation"]
                ),
                ModelInfo(
                    name="doubao-lite-4k-v1.0",
                    description="豆包轻量版模型，4K上下文",
                    context_length=4096,
                    priority=8,
                    capabilities=["text-generation", "fast-response"]
                )
            ]
        
        return PlatformModels(
            platform="火山豆包",
            models=models,
            updated_at=datetime.now().isoformat(),
            source_url=source_urls[0]
        )
    
    def get_moonshot_models(self) -> PlatformModels:
        """Get latest Moonshot models by calling their API."""
        logger.info("Fetching Moonshot models from API...")
        
        models = []
        source_url = "https://platform.moonshot.cn/docs/intro"
        api_url = "https://api.moonshot.cn/v1/models"
        
        try:
            # Try to get models from API first
            response = self.session.get(api_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for model_data in data['data']:
                        model_name = model_data.get('id', '')
                        if model_name.startswith('moonshot-'):
                            description = f"月之暗面模型 {model_name}"
                            context_length = None
                            
                            if '128k' in model_name:
                                context_length = 131072
                            elif '32k' in model_name:
                                context_length = 32768
                            elif '8k' in model_name:
                                context_length = 8192
                            
                            priority = 10
                            if '128k' in model_name:
                                priority = 15
                            elif '32k' in model_name:
                                priority = 12
                            elif '8k' in model_name:
                                priority = 8
                            
                            models.append(ModelInfo(
                                name=model_name,
                                description=f"{description} - {model_name}",
                                context_length=context_length,
                                priority=priority,
                                capabilities=["text-generation", "reasoning", "chinese"]
                            ))
            else:
                raise Exception(f"API returned status code {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to fetch Moonshot models from API: {e}")
            
            # Try scraping documentation as fallback
            try:
                response = self.session.get(source_url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                
                moonshot_pattern = r'(moonshot-v\d+-\d+k)'
                moonshot_matches = re.findall(moonshot_pattern, text_content.lower())
                
                if moonshot_matches:
                    for model_name in set(moonshot_matches):
                        description = f"月之暗面模型 {model_name}"
                        context_length = None
                        
                        if '128k' in model_name:
                            context_length = 131072
                        elif '32k' in model_name:
                            context_length = 32768
                        elif '8k' in model_name:
                            context_length = 8192
                        
                        priority = 10
                        if '128k' in model_name:
                            priority = 15
                        elif '32k' in model_name:
                            priority = 12
                        elif '8k' in model_name:
                            priority = 8
                        
                        models.append(ModelInfo(
                            name=model_name,
                            description=f"{description} - {model_name}",
                            context_length=context_length,
                            priority=priority,
                            capabilities=["text-generation", "reasoning", "chinese"]
                        ))
            
            except Exception as e2:
                logger.error(f"Failed to scrape Moonshot documentation: {e2}")
                # Final fallback to known models
                models = [
                    ModelInfo(
                        name="moonshot-v1-128k",
                        description="月之暗面128K超长上下文模型",
                        context_length=131072,
                        priority=15,
                        capabilities=["text-generation", "long-context", "chinese"]
                    ),
                    ModelInfo(
                        name="moonshot-v1-32k",
                        description="月之暗面32K标准模型",
                        context_length=32768,
                        priority=12,
                        capabilities=["text-generation", "reasoning", "chinese"]
                    ),
                    ModelInfo(
                        name="moonshot-v1-8k",
                        description="月之暗面8K基础模型",
                        context_length=8192,
                        priority=8,
                        capabilities=["text-generation", "fast-response", "chinese"]
                    )
                ]
        
        return PlatformModels(
            platform="月之暗面",
            models=models,
            updated_at=datetime.now().isoformat(),
            source_url=source_url
        )
    
    def get_deepseek_models(self) -> PlatformModels:
        """Get latest DeepSeek models by calling their API."""
        logger.info("Fetching DeepSeek models from API...")
        
        models = []
        source_url = "https://api-docs.deepseek.com/"
        api_url = "https://api.deepseek.com/v1/models"
        
        try:
            # Try to get models from API
            response = self.session.get(api_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for model_data in data['data']:
                        model_name = model_data.get('id', '')
                        if model_name.startswith('deepseek-'):
                            priority = 10
                            context_length = 32768
                            capabilities = ["text-generation"]
                            description = f"DeepSeek模型 {model_name}"
                            
                            if 'reasoner' in model_name or 'r1' in model_name:
                                priority = 15
                                description = f"DeepSeek推理模型 {model_name}"
                                capabilities = ["reasoning", "math", "logic"]
                            elif 'coder' in model_name:
                                priority = 12
                                description = f"DeepSeek编程模型 {model_name}"
                                capabilities = ["code-generation", "programming"]
                            elif 'chat' in model_name:
                                priority = 10
                                description = f"DeepSeek对话模型 {model_name}"
                                capabilities = ["text-generation", "conversation"]
                            
                            models.append(ModelInfo(
                                name=model_name,
                                description=description,
                                context_length=context_length,
                                priority=priority,
                                capabilities=capabilities
                            ))
            else:
                raise Exception(f"API returned status code {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to fetch DeepSeek models from API: {e}")
            
            # Try scraping documentation as fallback
            try:
                response = self.session.get(source_url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                
                deepseek_pattern = r'(deepseek-[a-zA-Z0-9\-]+)'
                deepseek_matches = re.findall(deepseek_pattern, text_content.lower())
                
                if deepseek_matches:
                    for model_name in set(deepseek_matches):
                        description = f"DeepSeek模型 {model_name}"
                        priority = 10
                        context_length = 32768
                        capabilities = ["text-generation"]
                        
                        if 'reasoner' in model_name or 'r1' in model_name:
                            priority = 15
                            description = f"DeepSeek推理模型 {model_name}"
                            capabilities = ["reasoning", "math", "logic"]
                        elif 'coder' in model_name:
                            priority = 12
                            description = f"DeepSeek编程模型 {model_name}"
                            capabilities = ["code-generation", "programming"]
                        elif 'chat' in model_name:
                            priority = 10
                            description = f"DeepSeek对话模型 {model_name}"
                            capabilities = ["text-generation", "conversation"]
                        
                        models.append(ModelInfo(
                            name=model_name,
                            description=description,
                            context_length=context_length,
                            priority=priority,
                            capabilities=capabilities
                        ))
            
            except Exception as e2:
                logger.error(f"Failed to scrape DeepSeek documentation: {e2}")
                # Final fallback to known models
                models = [
                    ModelInfo(
                        name="deepseek-reasoner",
                        description="DeepSeek R1推理模型",
                        context_length=32768,
                        priority=15,
                        capabilities=["reasoning", "math", "logic"]
                    ),
                    ModelInfo(
                        name="deepseek-chat",
                        description="DeepSeek V3对话模型",
                        context_length=32768,
                        priority=12,
                        capabilities=["text-generation", "conversation"]
                    ),
                    ModelInfo(
                        name="deepseek-coder",
                        description="DeepSeek编程专用模型",
                        context_length=16384,
                        priority=10,
                        capabilities=["code-generation", "programming"]
                    )
                ]
        
        return PlatformModels(
            platform="DeepSeek",
            models=models,
            updated_at=datetime.now().isoformat(),
            source_url=source_url
        )
    
    def get_ollama_models(self) -> PlatformModels:
        """Get popular Ollama models by calling local Ollama API."""
        logger.info("Fetching Ollama models from local API...")
        
        models = []
        source_url = "https://ollama.com/library"
        
        try:
            # Try to get models from local Ollama API
            local_api_url = "http://localhost:11434/api/tags"
            response = self.session.get(local_api_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'models' in data:
                    for model_data in data['models']:
                        model_name = model_data.get('name', '')
                        model_size = model_data.get('size', 0)
                        
                        description = f"Ollama本地模型 {model_name}"
                        capabilities = ["local-inference"]
                        priority = 10
                        context_length = 8192
                        
                        if 'llama' in model_name.lower():
                            description = f"Llama系列本地模型 {model_name}"
                            capabilities = ["text-generation", "conversation", "local-inference"]
                            priority = 12
                            context_length = 8192
                        elif 'qwen' in model_name.lower():
                            description = f"通义千问本地模型 {model_name}"
                            capabilities = ["text-generation", "chinese", "local-inference"]
                            priority = 12
                            context_length = 32768
                        elif 'deepseek' in model_name.lower():
                            description = f"DeepSeek本地模型 {model_name}"
                            capabilities = ["reasoning", "local-inference"]
                            priority = 15
                            context_length = 32768
                        
                        models.append(ModelInfo(
                            name=model_name,
                            description=description,
                            context_length=context_length,
                            priority=priority,
                            capabilities=capabilities
                        ))
            else:
                raise Exception(f"Local Ollama API not available")
        
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models from local API: {e}")
            
            # Try scraping Ollama library page as fallback
            try:
                response = self.session.get(source_url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for model links or model names
                # This is a simplified approach - real implementation would need 
                # to analyze Ollama's specific HTML structure
                
                # Popular models as fallback
                models = [
                    ModelInfo(
                        name="deepseek-r1:8b",
                        description="DeepSeek R1 8B本地推理模型",
                        context_length=32768,
                        priority=15,
                        capabilities=["reasoning", "math", "local-inference"]
                    ),
                    ModelInfo(
                        name="llama3.2:latest",
                        description="Meta Llama 3.2最新版本",
                        context_length=8192,
                        priority=12,
                        capabilities=["text-generation", "conversation", "local-inference"]
                    ),
                    ModelInfo(
                        name="qwen2.5:latest",
                        description="通义千问2.5开源版本",
                        context_length=32768,
                        priority=12,
                        capabilities=["text-generation", "chinese", "local-inference"]
                    )
                ]
            
            except Exception as e2:
                logger.error(f"Failed to scrape Ollama library: {e2}")
                # Final fallback to known popular models
                models = [
                    ModelInfo(
                        name="deepseek-r1:8b",
                        description="DeepSeek R1 8B本地推理模型",
                        context_length=32768,
                        priority=15,
                        capabilities=["reasoning", "math", "local-inference"]
                    ),
                    ModelInfo(
                        name="llama3.2:latest",
                        description="Meta Llama 3.2最新版本",
                        context_length=8192,
                        priority=12,
                        capabilities=["text-generation", "conversation", "local-inference"]
                    ),
                    ModelInfo(
                        name="qwen2.5:latest",
                        description="通义千问2.5开源版本",
                        context_length=32768,
                        priority=12,
                        capabilities=["text-generation", "chinese", "local-inference"]
                    )
                ]
        
        return PlatformModels(
            platform="Ollama",
            models=models,
            updated_at=datetime.now().isoformat(),
            source_url=source_url
        )
    
    def get_all_platforms_models(self) -> Dict[str, PlatformModels]:
        """Get models for all platforms."""
        platforms = {}
        
        # Add delay between requests to be respectful
        platform_methods = [
            ("alibaba", self.get_alibaba_models),
            ("doubao", self.get_doubao_models),
            ("moonshot", self.get_moonshot_models),
            ("deepseek", self.get_deepseek_models),
            ("ollama", self.get_ollama_models),
        ]
        
        for platform_name, method in platform_methods:
            try:
                logger.info(f"Fetching models for {platform_name}...")
                platforms[platform_name] = method()
                # Add delay between requests
                time.sleep(1)
            except Exception as e:
                logger.error(f"Failed to fetch {platform_name} models: {e}")
        
        return platforms
    
    def update_env_example(self, platforms_models: Dict[str, PlatformModels], env_file_path: str = "env.example") -> str:
        """Update .env.example file with latest models."""
        logger.info("Updating .env.example with latest models...")
        
        # Read current env.example
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"File {env_file_path} not found")
            return f"❌ 文件 {env_file_path} 不存在"
        
        # Update model configurations
        updated_content = content
        
        # Update Alibaba models - use top 3 models
        if "alibaba" in platforms_models:
            platform_models = platforms_models["alibaba"]
            top_models = platform_models.get_top_models(3)
            if top_models:
                pattern = r'(ALIBABA_MODEL=)[^\n]*'
                replacement = f'ALIBABA_MODEL={top_models[0].name}'
                updated_content = re.sub(pattern, replacement, updated_content)
                
                # Update model comments with top 3 models
                alibaba_section = self._generate_alibaba_section(top_models)
                pattern = r'(# 推荐模型选项 \(2025年最新\):.*?ALIBABA_MODEL=)[^\n]*'
                replacement = f'{alibaba_section}ALIBABA_MODEL={top_models[0].name}'
                updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        
        # Update Doubao models - use top 3 models
        if "doubao" in platforms_models:
            platform_models = platforms_models["doubao"]
            top_models = platform_models.get_top_models(3)
            if top_models:
                # Use endpoint format for Doubao
                best_model = top_models[0].name
                if best_model.startswith("doubao-"):
                    endpoint_name = f"ep-{best_model.replace('doubao-', '').replace('.', '-')}"
                else:
                    endpoint_name = best_model
                pattern = r'(DOUBAO_MODEL=)[^\n]*'
                replacement = f'DOUBAO_MODEL={endpoint_name}'
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Update Moonshot models - use top 3 models
        if "moonshot" in platforms_models:
            platform_models = platforms_models["moonshot"]
            top_models = platform_models.get_top_models(3)
            if top_models:
                pattern = r'(MOONSHOT_MODEL=)[^\n]*'
                replacement = f'MOONSHOT_MODEL={top_models[0].name}'
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Update DeepSeek models - use top 3 models
        if "deepseek" in platforms_models:
            platform_models = platforms_models["deepseek"]
            top_models = platform_models.get_top_models(3)
            if top_models:
                pattern = r'(DEEPSEEK_MODEL=)[^\n]*'
                replacement = f'DEEPSEEK_MODEL={top_models[0].name}'
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Update Ollama models - use top 3 models
        if "ollama" in platforms_models:
            platform_models = platforms_models["ollama"]
            top_models = platform_models.get_top_models(3)
            if top_models:
                pattern = r'(OLLAMA_MODEL=)[^\n]*'
                replacement = f'OLLAMA_MODEL={top_models[0].name}'
                updated_content = re.sub(pattern, replacement, updated_content)
        
        # Add update timestamp
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_content = f"# 最后更新时间: {update_time}\n# 自动更新的最新模型配置\n\n{updated_content}"
        
        # Write updated content back
        try:
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            logger.info(f"Successfully updated {env_file_path}")
            return f"✅ 成功更新 {env_file_path}，包含最新模型配置"
        except Exception as e:
            logger.error(f"Failed to write {env_file_path}: {e}")
            return f"❌ 写入文件失败: {e}"
    
    def _generate_alibaba_section(self, models: List[ModelInfo]) -> str:
        """Generate Alibaba model section with latest models."""
        lines = ["# 推荐模型选项 (2025年最新):"]
        for model in models:
            context_info = f"，{model.context_length//1024}K上下文" if model.context_length else ""
            lines.append(f"# - {model.name:<30} ({model.description.split('，')[0]}{context_info})")
        lines.append("")
        return "\n".join(lines) + "\n"
    
    def generate_models_report(self, platforms_models: Dict[str, PlatformModels]) -> str:
        """Generate a detailed models report with top 3 models per platform."""
        report = ["# 最新LLM模型报告", ""]
        report.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for platform_key, platform_data in platforms_models.items():
            report.append(f"## {platform_data.platform}")
            report.append(f"来源: {platform_data.source_url}")
            report.append("")
            
            # Get top 3 models for this platform
            top_models = platform_data.get_top_models(3)
            
            if top_models:
                report.append("### 🏆 推荐模型（按优先级排序）")
                report.append("")
                
                for i, model in enumerate(top_models, 1):
                    report.append(f"#### {i}. {model.name}")
                    report.append(f"- **描述**: {model.description}")
                    if model.context_length:
                        report.append(f"- **上下文长度**: {model.context_length:,} tokens")
                    if model.release_date:
                        report.append(f"- **发布日期**: {model.release_date}")
                    if model.capabilities:
                        report.append(f"- **能力**: {', '.join(model.capabilities)}")
                    report.append(f"- **优先级**: {model.priority}")
                    report.append("")
                
                # Show additional models if there are more than 3
                if len(platform_data.models) > 3:
                    remaining_count = len(platform_data.models) - 3
                    report.append(f"*还有 {remaining_count} 个其他模型可用*")
                    report.append("")
            else:
                report.append("⚠️ 暂无可用模型")
                report.append("")
            
            report.append("")
        
        return "\n".join(report) 
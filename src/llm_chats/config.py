"""Configuration management for LLM platforms."""
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from dataclasses import dataclass
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    name: str
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError(f"API key is required for {self.name}")


# 更新后的平台配置 - 基于实际开通的模型信息
@dataclass
class PlatformConfigs:
    alibaba_config: Optional[LLMConfig] = None
    doubao_config: Optional[LLMConfig] = None  
    moonshot_config: Optional[LLMConfig] = None
    deepseek_config: Optional[LLMConfig] = None
    ollama_config: Optional[LLMConfig] = None
    
    @classmethod
    def from_env(cls) -> 'PlatformConfigs':
        """从环境变量创建配置"""
        # 阿里云百炼 - 推荐模型
        alibaba_config = None
        alibaba_key = os.getenv('ALIBABA_API_KEY')
        if alibaba_key:
            try:
                alibaba_config = LLMConfig(
                    name="阿里云百炼",
                    model=os.getenv('ALIBABA_MODEL', 'qwen-max-2024-09-19'),  
                    api_key=alibaba_key,
                    base_url=os.getenv('ALIBABA_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                    temperature=float(os.getenv('ALIBABA_TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('ALIBABA_MAX_TOKENS', '1000'))
                )
            except ValueError as e:
                logger.warning(f"阿里云百炼配置错误: {e}")
        
        # 火山豆包 - 使用实际开通的接入点
        # 根据文档已开通的模型：doubao-seed-1-6-250615，接入点：ep-m-20250629223026-prr94
        doubao_config = None
        doubao_key = os.getenv('DOUBAO_API_KEY')
        if doubao_key:
            try:
                doubao_config = LLMConfig(
                    name="火山豆包",
                    model=os.getenv('DOUBAO_MODEL', 'ep-m-20250629223026-prr94'),  # 使用实际接入点
                    api_key=doubao_key,
                    base_url=os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
                    temperature=float(os.getenv('DOUBAO_TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('DOUBAO_MAX_TOKENS', '1000'))
                )
            except ValueError as e:
                logger.warning(f"火山豆包配置错误: {e}")
        
        # 月之暗面 - 推荐模型  
        moonshot_config = None
        moonshot_key = os.getenv('MOONSHOT_API_KEY')
        if moonshot_key:
            try:
                moonshot_config = LLMConfig(
                    name="月之暗面",
                    model=os.getenv('MOONSHOT_MODEL', 'moonshot-v1-128k'),  
                    api_key=moonshot_key,
                    base_url=os.getenv('MOONSHOT_BASE_URL', 'https://api.moonshot.cn/v1'),
                    temperature=float(os.getenv('MOONSHOT_TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('MOONSHOT_MAX_TOKENS', '1000'))
                )
            except ValueError as e:
                logger.warning(f"月之暗面配置错误: {e}")
        
        # DeepSeek - 推荐模型
        deepseek_config = None
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if deepseek_key:
            try:
                deepseek_config = LLMConfig(
                    name="DeepSeek",
                    model=os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner'),  
                    api_key=deepseek_key,
                    base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
                    temperature=float(os.getenv('DEEPSEEK_TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('DEEPSEEK_MAX_TOKENS', '1000'))
                )
            except ValueError as e:
                logger.warning(f"DeepSeek配置错误: {e}")
        
        # Ollama - 本地模型
        ollama_config = None
        ollama_enabled = os.getenv('OLLAMA_ENABLED', 'false').lower() == 'true'
        if ollama_enabled:
            try:
                # 智能处理 base_url，自动添加 /v1 后缀
                base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
                if not base_url.endswith('/v1'):
                    base_url = base_url.rstrip('/') + '/v1'
                
                ollama_config = LLMConfig(
                    name="Ollama",
                    model=os.getenv('OLLAMA_MODEL', 'deepseek-r1:8b'),  # 使用实际可用的模型
                    api_key=os.getenv('OLLAMA_API_KEY', 'ollama'),  # Ollama doesn't require API key
                    base_url=base_url,
                    temperature=float(os.getenv('OLLAMA_TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('OLLAMA_MAX_TOKENS', '1000'))
                )
                logger.info(f"Ollama配置: {base_url}, 模型: {ollama_config.model}")
            except ValueError as e:
                logger.warning(f"Ollama配置错误: {e}")
        
        return cls(
            alibaba_config=alibaba_config,
            doubao_config=doubao_config,
            moonshot_config=moonshot_config, 
            deepseek_config=deepseek_config,
            ollama_config=ollama_config
        )
    
    def get_enabled_platforms(self) -> Dict[str, LLMConfig]:
        """获取已启用的平台配置字典"""
        enabled = {}
        if self.alibaba_config:
            enabled['alibaba'] = self.alibaba_config
        if self.doubao_config:
            enabled['doubao'] = self.doubao_config
        if self.moonshot_config:
            enabled['moonshot'] = self.moonshot_config
        if self.deepseek_config:
            enabled['deepseek'] = self.deepseek_config
        if self.ollama_config:
            enabled['ollama'] = self.ollama_config
        return enabled
    
    def get_enabled_configs(self) -> List[LLMConfig]:
        """获取已启用的配置列表"""
        return list(self.get_enabled_platforms().values())
    
    def count_enabled(self) -> int:
        """获取已启用的平台数量"""
        return len(self.get_enabled_platforms())


def get_config() -> PlatformConfigs:
    """Get platform configurations."""
    return PlatformConfigs.from_env() 
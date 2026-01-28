# -*- coding: utf-8 -*-
"""
AI 提供商管理模块
支持多家 AI 大模型：DeepSeek、OpenAI、通义千问、Ollama

作者: GDH
"""

from openai import OpenAI
from typing import Tuple, Optional, Dict, List
from abc import ABC, abstractmethod
import json


class AIProviderBase(ABC):
    """AI 提供商基类"""
    
    def __init__(self, name: str, base_url: str, default_model: str):
        self.name = name
        self.base_url = base_url
        self.default_model = default_model
        self.api_key = ""
        self.client: Optional[OpenAI] = None
    
    def configure(self, api_key: str, model: str = None) -> bool:
        """配置 API Key"""
        try:
            self.api_key = api_key
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
            if model:
                self.default_model = model
            return True
        except Exception as e:
            print(f"配置 {self.name} 失败: {e}")
            return False
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.client is not None
    
    def get_system_prompt(self, os_type: str, server_info: str, memory_context: str) -> str:
        """生成系统提示词"""
        return f"""你是一个专业且友好的 Linux 系统运维专家。你就像用户的老朋友一样，熟悉他们的服务器环境和操作习惯。

【当前服务器信息】
{server_info}

【操作系统类型】
{os_type}

【历史操作记录】
{memory_context if memory_context else "这是首次操作此服务器"}

【你的职责】
1. 将用户的自然语言需求转换为准确的 Linux 命令
2. 根据操作系统类型选择正确的包管理器和命令格式：
   - Ubuntu/Debian: 使用 apt
   - CentOS/RHEL/Fedora: 使用 yum 或 dnf
   - Alpine: 使用 apk
3. 结合历史操作记录，理解用户可能的意图
4. 像朋友一样关心服务器的健康状态

【响应格式】
只返回 JSON 格式：
{{
    "command": "要执行的命令",
    "description": "简短描述",
    "dangerous": false,
    "explanation": "详细解释",
    "friendly_note": "像朋友一样的温馨提示（可选）"
}}

如果需要更多信息，返回：
{{
    "command": "",
    "description": "需要更多信息",
    "dangerous": false,
    "explanation": "具体需要什么信息",
    "friendly_note": ""
}}
"""

    def parse_command(self, user_input: str, os_type: str = "Linux", 
                     server_info: str = "", memory_context: str = "") -> Tuple[str, str, bool, str, str]:
        """
        解析用户输入
        
        Returns:
            (命令, 描述, 是否危险, 解释, 友好提示)
        """
        if not self.is_configured():
            return "", "AI 未配置", False, f"请先设置 {self.name} API Key", ""
        
        try:
            system_prompt = self.get_system_prompt(os_type, server_info, memory_context)
            
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 处理 markdown 代码块
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            
            result = json.loads(content)
            
            return (
                result.get("command", ""),
                result.get("description", ""),
                result.get("dangerous", False),
                result.get("explanation", ""),
                result.get("friendly_note", "")
            )
            
        except json.JSONDecodeError:
            return "", "AI 响应解析失败", False, "无法解析 AI 响应", ""
        except Exception as e:
            return "", "AI 调用失败", False, str(e), ""


class DeepSeekProvider(AIProviderBase):
    """DeepSeek 提供商"""
    def __init__(self):
        super().__init__(
            name="DeepSeek",
            base_url="https://api.deepseek.com",
            default_model="deepseek-chat"
        )


class OpenAIProvider(AIProviderBase):
    """OpenAI 提供商"""
    def __init__(self):
        super().__init__(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            default_model="gpt-4o-mini"
        )


class QwenProvider(AIProviderBase):
    """通义千问提供商"""
    def __init__(self):
        super().__init__(
            name="通义千问",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            default_model="qwen-turbo"
        )


class OllamaProvider(AIProviderBase):
    """Ollama 本地提供商"""
    def __init__(self):
        super().__init__(
            name="Ollama",
            base_url="http://localhost:11434/v1",
            default_model="qwen2.5:7b"
        )
    
    def configure(self, api_key: str = "ollama", model: str = None) -> bool:
        """Ollama 不需要真正的 API Key"""
        try:
            self.api_key = "ollama"
            self.client = OpenAI(
                api_key="ollama",
                base_url=self.base_url
            )
            if model:
                self.default_model = model
            return True
        except Exception as e:
            print(f"配置 Ollama 失败: {e}")
            return False


class AIProviderManager:
    """AI 提供商管理器"""
    
    PROVIDERS = {
        "DeepSeek": DeepSeekProvider,
        "OpenAI": OpenAIProvider,
        "通义千问": QwenProvider,
        "Ollama": OllamaProvider
    }
    
    def __init__(self):
        self.providers: Dict[str, AIProviderBase] = {}
        self.current_provider: Optional[str] = None
        
        # 初始化所有提供商
        for name, cls in self.PROVIDERS.items():
            self.providers[name] = cls()
    
    def get_provider_names(self) -> List[str]:
        """获取所有提供商名称"""
        return list(self.PROVIDERS.keys())
    
    def configure_provider(self, name: str, api_key: str, model: str = None) -> bool:
        """配置指定提供商"""
        if name not in self.providers:
            return False
        return self.providers[name].configure(api_key, model)
    
    def set_current_provider(self, name: str) -> bool:
        """设置当前使用的提供商"""
        if name in self.providers and self.providers[name].is_configured():
            self.current_provider = name
            return True
        return False
    
    def get_current_provider(self) -> Optional[AIProviderBase]:
        """获取当前提供商"""
        if self.current_provider:
            return self.providers.get(self.current_provider)
        return None
    
    def is_configured(self) -> bool:
        """检查是否有可用的提供商"""
        return self.current_provider is not None
    
    def parse_command(self, user_input: str, os_type: str = "Linux",
                     server_info: str = "", memory_context: str = "") -> Tuple[str, str, bool, str, str]:
        """使用当前提供商解析命令"""
        provider = self.get_current_provider()
        if not provider:
            return "", "未配置 AI", False, "请先选择并配置 AI 提供商", ""
        return provider.parse_command(user_input, os_type, server_info, memory_context)

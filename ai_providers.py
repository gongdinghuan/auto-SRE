# -*- coding: utf-8 -*-
"""
AI 提供商管理模块
支持多家 AI 大模型：DeepSeek、OpenAI、通义千问、Ollama
支持多轮对话和上下文连续

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
        try:
            self.api_key = api_key
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
            if model:
                self.default_model = model
            return True
        except Exception as e:
            print(f"配置 {self.name} 失败: {e}")
            return False
    
    def is_configured(self) -> bool:
        return self.client is not None
    
    def get_system_prompt(self, os_type: str, server_info: str, memory_context: str) -> str:
        return f"""你是一个专业、友好且极其聪明的 Linux 系统运维专家。你是用户的贴心老朋友，完全了解他们的服务器环境和操作习惯。

【当前服务器信息】
{server_info}

【操作系统】{os_type}

【历史操作上下文】
{memory_context}

【你的核心能力】
1. **理解复杂意图**: 能理解模糊、复杂的自然语言需求，结合上下文推断用户真正想要什么
2. **上下文连续性**: 记住之前的操作和输出，用户说"再看看"、"那个进程"、"刚才的"你都能理解
3. **智能命令生成**: 根据 {os_type} 系统选择正确的命令（apt/yum/dnf/apk）
4. **主动关怀**: 发现问题会主动提醒，像朋友一样关心服务器健康
5. **多步骤任务**: 能处理需要多个命令的复杂任务

【上下文理解示例】
- 用户: "内存占用最高的是什么" → 你执行 ps 命令显示了结果
- 用户: "杀掉它" → 你应该理解是要杀掉之前显示的那个进程
- 用户: "再查一遍" → 重复上一个命令
- 用户: "那个服务重启一下" → 根据之前提到的服务来操作

【响应格式】
返回 JSON 格式：
{{
    "command": "要执行的命令（如需多条用 && 连接）",
    "description": "简短描述你要做什么",
    "dangerous": false,
    "explanation": "为什么这样做",
    "friendly_note": "给用户的贴心提示或关心的话",
    "follow_up": "可选的后续建议"
}}

如果需要用户提供更多信息：
{{
    "command": "",
    "description": "需要确认",
    "dangerous": false,
    "explanation": "具体需要确认什么",
    "friendly_note": "友好的询问",
    "follow_up": ""
}}

【重要原则】
- 始终保持友好、专业的语气
- 危险操作（rm -rf、reboot、dd等）必须设 dangerous 为 true
- 复杂任务可以合并多条命令
- 不确定时宁可多问一句"""

    def parse_command(self, user_input: str, os_type: str = "Linux", 
                     server_info: str = "", memory_context: str = "",
                     session_messages: List[Dict] = None) -> Tuple[str, str, bool, str, str, str]:
        """
        解析用户输入（支持多轮对话）
        
        Args:
            user_input: 用户输入
            os_type: 操作系统类型
            server_info: 服务器信息
            memory_context: 历史操作上下文
            session_messages: 会话消息列表（多轮对话）
        
        Returns:
            (命令, 描述, 是否危险, 解释, 友好提示, 后续建议)
        """
        if not self.is_configured():
            return "", "AI 未配置", False, f"请先设置 {self.name} API Key", "", ""
        
        try:
            system_prompt = self.get_system_prompt(os_type, server_info, memory_context)
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加会话历史（多轮对话）
            if session_messages:
                for msg in session_messages[-10:]:  # 最近5轮对话
                    messages.append(msg)
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=0.1,
                max_tokens=800
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
                result.get("friendly_note", ""),
                result.get("follow_up", "")
            )
            
        except json.JSONDecodeError:
            return "", "AI 响应解析失败", False, "无法解析 AI 响应", "", ""
        except Exception as e:
            return "", "AI 调用失败", False, str(e), "", ""
    
    def analyze_output(self, user_input: str, command: str, output: str, 
                      os_type: str = "Linux", server_info: str = "") -> str:
        """
        分析命令输出并生成解读
        
        Args:
            user_input: 用户原始请求
            command: 执行的命令
            output: 命令输出
            os_type: 操作系统类型
            server_info: 服务器信息
        
        Returns:
            AI 对输出的解读和总结
        """
        if not self.is_configured():
            return ""
        
        try:
            prompt = f"""你是一个专业的 Linux 运维专家，请分析以下命令的输出结果，用简洁友好的中文回答用户。

【用户请求】{user_input}
【执行命令】{command}
【操作系统】{os_type}
【服务器信息】{server_info}

【命令输出】
{output[:2000]}

【要求】
1. 简洁明了地解读输出结果，直接回答用户的问题
2. 如果发现异常或问题，主动指出并给出建议
3. 用友好、口语化的方式表达，像朋友聊天一样
4. 如果输出很长，提取关键信息进行总结
5. 可以用 emoji 让回复更生动
6. 回复控制在 200 字以内

直接回复解读内容，不要返回 JSON。"""

            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return ""


class DeepSeekProvider(AIProviderBase):
    def __init__(self):
        super().__init__("DeepSeek", "https://api.deepseek.com", "deepseek-chat")


class OpenAIProvider(AIProviderBase):
    def __init__(self):
        super().__init__("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini")


class QwenProvider(AIProviderBase):
    def __init__(self):
        super().__init__("通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-turbo")


class OllamaProvider(AIProviderBase):
    def __init__(self):
        super().__init__("Ollama", "http://localhost:11434/v1", "qwen2.5:7b")
    
    def configure(self, api_key: str = "ollama", model: str = None) -> bool:
        try:
            self.api_key = "ollama"
            self.client = OpenAI(api_key="ollama", base_url=self.base_url)
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
        
        for name, cls in self.PROVIDERS.items():
            self.providers[name] = cls()
    
    def get_provider_names(self) -> List[str]:
        return list(self.PROVIDERS.keys())
    
    def configure_provider(self, name: str, api_key: str, model: str = None) -> bool:
        if name not in self.providers:
            return False
        return self.providers[name].configure(api_key, model)
    
    def set_current_provider(self, name: str) -> bool:
        if name in self.providers and self.providers[name].is_configured():
            self.current_provider = name
            return True
        return False
    
    def get_current_provider(self) -> Optional[AIProviderBase]:
        if self.current_provider:
            return self.providers.get(self.current_provider)
        return None
    
    def is_configured(self) -> bool:
        return self.current_provider is not None
    
    def parse_command(self, user_input: str, os_type: str = "Linux",
                     server_info: str = "", memory_context: str = "",
                     session_messages: List[Dict] = None) -> Tuple[str, str, bool, str, str, str]:
        """使用当前提供商解析命令（支持多轮对话）"""
        provider = self.get_current_provider()
        if not provider:
            return "", "未配置 AI", False, "请先选择并配置 AI 提供商", "", ""
        return provider.parse_command(user_input, os_type, server_info, memory_context, session_messages)
    
    def analyze_output(self, user_input: str, command: str, output: str,
                      os_type: str = "Linux", server_info: str = "") -> str:
        """使用当前提供商分析命令输出"""
        provider = self.get_current_provider()
        if not provider:
            return ""
        return provider.analyze_output(user_input, command, output, os_type, server_info)

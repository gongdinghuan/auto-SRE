# -*- coding: utf-8 -*-
"""
DeepSeek AI 模块
使用 DeepSeek 大模型解析自然语言并生成 Linux 命令
"""

from openai import OpenAI
from typing import Tuple, Optional
import json


class DeepSeekAI:
    """DeepSeek AI 助手"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.client: Optional[OpenAI] = None
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com"
        
        # 系统提示词
        self.system_prompt = """你是一个专业的 Linux 系统运维专家。你的任务是将用户的自然语言需求转换为准确的 Linux 命令。

规则：
1. 只返回 JSON 格式的响应，包含以下字段：
   - "command": 要执行的 Linux 命令（如果需要多个命令，用 && 或 ; 连接）
   - "description": 命令的简短描述
   - "dangerous": 是否是危险命令（布尔值），危险命令包括：reboot, shutdown, rm -rf, mkfs, dd 等
   - "explanation": 对命令的详细解释

2. 如果用户的需求不明确或无法转换为命令，返回：
   - "command": ""
   - "description": "需要更多信息"
   - "explanation": 解释为什么需要更多信息

3. 始终考虑命令的安全性，对于危险操作要标记 dangerous 为 true

4. 命令应该是可以直接在 Linux shell 中执行的

示例输入："查看内存使用情况"
示例输出：
{
    "command": "free -h",
    "description": "查看内存使用情况",
    "dangerous": false,
    "explanation": "使用 free 命令显示系统内存使用情况，-h 参数使输出更易读"
}

示例输入："删除 /tmp 下所有文件"
示例输出：
{
    "command": "rm -rf /tmp/*",
    "description": "删除 /tmp 目录下所有文件",
    "dangerous": true,
    "explanation": "使用 rm -rf 递归强制删除 /tmp 下的所有文件和目录。这是危险操作，可能会删除重要的临时文件。"
}
"""
    
    def set_api_key(self, api_key: str) -> bool:
        """设置 API Key 并初始化客户端"""
        if not api_key or not api_key.strip():
            return False
        
        self.api_key = api_key.strip()
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            return True
        except Exception as e:
            print(f"初始化 DeepSeek 客户端失败: {e}")
            return False
    
    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return self.client is not None and self.api_key != ""
    
    def parse_command(self, user_input: str) -> Tuple[str, str, bool, str]:
        """
        使用 AI 解析用户输入
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            (命令, 描述, 是否危险, 解释)
        """
        if not self.is_configured():
            return "", "AI 未配置", False, "请先设置 DeepSeek API Key"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析 JSON
            # 处理可能的 markdown 代码块
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            
            result = json.loads(content)
            
            command = result.get("command", "")
            description = result.get("description", "")
            dangerous = result.get("dangerous", False)
            explanation = result.get("explanation", "")
            
            return command, description, dangerous, explanation
            
        except json.JSONDecodeError as e:
            return "", "AI 响应解析失败", False, f"无法解析 AI 响应: {str(e)}"
        except Exception as e:
            return "", "AI 调用失败", False, f"错误: {str(e)}"
    
    def chat(self, user_input: str, context: str = "") -> str:
        """
        与 AI 进行对话（用于更复杂的交互）
        
        Args:
            user_input: 用户输入
            context: 上下文信息（如当前服务器状态）
            
        Returns:
            AI 的回复
        """
        if not self.is_configured():
            return "请先设置 DeepSeek API Key"
        
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的 Linux 系统运维专家，帮助用户解决服务器运维问题。"}
            ]
            
            if context:
                messages.append({"role": "user", "content": f"当前系统状态：\n{context}"})
                messages.append({"role": "assistant", "content": "好的，我已经了解当前系统状态。请问有什么可以帮助您的？"})
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI 调用失败: {str(e)}"

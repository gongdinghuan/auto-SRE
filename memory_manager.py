# -*- coding: utf-8 -*-
"""
服务器操作记忆管理模块
按服务器 IP 存储操作历史，提供丰富的上下文支持
支持会话级别的对话历史

作者: GDH
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class MemoryManager:
    """服务器操作记忆管理器 - 增强版"""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        self.current_ip: Optional[str] = None
        self.current_memory: List[Dict] = []
        self.max_context_items = 15  # 发送给 AI 的最大历史条数
        self.max_output_chars = 1000  # 每条输出最大字符数
        
        # 会话对话历史（用于多轮对话）
        self.session_history: List[Dict] = []
        self.max_session_turns = 10  # 最大会话轮数
        
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
    
    def _get_memory_file(self, ip: str) -> str:
        safe_ip = ip.replace(".", "_").replace(":", "_")
        return os.path.join(self.memory_dir, f"{safe_ip}.json")
    
    def load_memory(self, ip: str) -> List[Dict]:
        """加载指定服务器的记忆"""
        self.current_ip = ip
        self.session_history = []  # 重置会话历史
        memory_file = self._get_memory_file(ip)
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_memory = data.get("history", [])
            except (json.JSONDecodeError, IOError):
                self.current_memory = []
        else:
            self.current_memory = []
        
        return self.current_memory
    
    def save_memory(self):
        """保存当前服务器的记忆"""
        if not self.current_ip:
            return
        
        memory_file = self._get_memory_file(self.current_ip)
        data = {
            "ip": self.current_ip,
            "last_updated": datetime.now().isoformat(),
            "total_operations": len(self.current_memory),
            "history": self.current_memory
        }
        
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存记忆失败: {e}")
    
    def add_operation(self, user_input: str, command: str, output: str, success: bool):
        """添加一条操作记录（包含完整输出）"""
        # 截取输出但保留更多内容
        truncated_output = output[:self.max_output_chars]
        if len(output) > self.max_output_chars:
            truncated_output += f"\n... (共 {len(output)} 字符，已截取前 {self.max_output_chars} 字符)"
        
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": user_input,
            "command": command,
            "output": truncated_output,
            "output_length": len(output),
            "success": success
        }
        
        self.current_memory.append(record)
        
        # 同时添加到会话历史
        self.session_history.append({
            "role": "user",
            "content": user_input
        })
        self.session_history.append({
            "role": "assistant", 
            "content": f"执行命令: {command}\n输出:\n{truncated_output}"
        })
        
        # 限制会话历史长度
        if len(self.session_history) > self.max_session_turns * 2:
            self.session_history = self.session_history[-(self.max_session_turns * 2):]
        
        # 保持最多200条持久化记录
        if len(self.current_memory) > 200:
            self.current_memory = self.current_memory[-200:]
        
        self.save_memory()
    
    def add_ai_response(self, ai_response: str):
        """添加 AI 的分析响应到会话"""
        if self.session_history and self.session_history[-1]["role"] == "assistant":
            # 追加到上一条助手消息
            self.session_history[-1]["content"] += f"\n\nAI分析: {ai_response}"
        else:
            self.session_history.append({
                "role": "assistant",
                "content": ai_response
            })
    
    def get_session_messages(self) -> List[Dict]:
        """获取会话消息列表（用于多轮对话）"""
        return self.session_history.copy()
    
    def get_context_for_ai(self) -> str:
        """获取发送给 AI 的丰富上下文"""
        if not self.current_memory:
            return "这是首次操作此服务器，暂无历史记录。"
        
        recent = self.current_memory[-self.max_context_items:]
        
        context_lines = [
            f"【服务器操作历史】共 {len(self.current_memory)} 条记录，以下是最近 {len(recent)} 条：",
            ""
        ]
        
        for i, record in enumerate(recent, 1):
            status = "✅ 成功" if record.get("success", True) else "❌ 失败"
            time_str = record.get("time", "")
            user_input = record.get("input", "")
            command = record.get("command", "")
            output = record.get("output", "")
            
            context_lines.append(f"--- 操作 {i} [{time_str}] {status} ---")
            context_lines.append(f"用户请求: {user_input}")
            context_lines.append(f"执行命令: {command}")
            
            # 包含输出摘要
            if output:
                # 取前几行输出
                output_lines = output.split('\n')[:5]
                output_preview = '\n'.join(output_lines)
                if len(output_lines) < len(output.split('\n')):
                    output_preview += "\n..."
                context_lines.append(f"输出摘要:\n{output_preview}")
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def get_last_output(self) -> str:
        """获取最近一次命令的输出"""
        if self.current_memory:
            return self.current_memory[-1].get("output", "")
        return ""
    
    def get_last_command(self) -> str:
        """获取最近一次执行的命令"""
        if self.current_memory:
            return self.current_memory[-1].get("command", "")
        return ""
    
    def get_friendly_summary(self) -> str:
        """获取友好的记忆摘要"""
        if not self.current_memory:
            return "首次连接此服务器"
        
        count = len(self.current_memory)
        last = self.current_memory[-1]
        last_time = last.get("time", "未知")
        success_count = sum(1 for r in self.current_memory if r.get("success", True))
        
        return f"已有 {count} 条记录 (成功 {success_count} 次)，上次: {last_time}"
    
    def search_history(self, keyword: str) -> List[Dict]:
        """搜索历史操作"""
        results = []
        keyword_lower = keyword.lower()
        
        for record in self.current_memory:
            if (keyword_lower in record.get("input", "").lower() or
                keyword_lower in record.get("command", "").lower() or
                keyword_lower in record.get("output", "").lower()):
                results.append(record)
        
        return results
    
    def clear_session(self):
        """清空当前会话历史（保留持久化记忆）"""
        self.session_history = []
    
    def clear_memory(self, ip: str = None):
        """清空指定服务器的所有记忆"""
        target_ip = ip or self.current_ip
        if not target_ip:
            return
        
        memory_file = self._get_memory_file(target_ip)
        if os.path.exists(memory_file):
            try:
                os.remove(memory_file)
            except IOError:
                pass
        
        if target_ip == self.current_ip:
            self.current_memory = []
            self.session_history = []

# -*- coding: utf-8 -*-
"""
服务器操作记忆管理模块
按服务器 IP 存储操作历史，提供上下文支持

作者: GDH
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class MemoryManager:
    """服务器操作记忆管理器"""
    
    def __init__(self, memory_dir: str = "memory"):
        """
        初始化记忆管理器
        
        Args:
            memory_dir: 记忆存储目录
        """
        self.memory_dir = memory_dir
        self.current_ip: Optional[str] = None
        self.current_memory: List[Dict] = []
        self.max_context_items = 10  # 发送给 AI 的最大历史条数
        
        # 确保记忆目录存在
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
    
    def _get_memory_file(self, ip: str) -> str:
        """获取记忆文件路径"""
        # 将 IP 中的点替换为下划线
        safe_ip = ip.replace(".", "_").replace(":", "_")
        return os.path.join(self.memory_dir, f"{safe_ip}.json")
    
    def load_memory(self, ip: str) -> List[Dict]:
        """加载指定服务器的记忆"""
        self.current_ip = ip
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
            "history": self.current_memory
        }
        
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存记忆失败: {e}")
    
    def add_operation(self, user_input: str, command: str, output: str, success: bool):
        """
        添加一条操作记录
        
        Args:
            user_input: 用户的自然语言输入
            command: 执行的命令
            output: 命令输出（截取前500字符）
            success: 是否成功
        """
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": user_input,
            "command": command,
            "output": output[:500] if len(output) > 500 else output,
            "success": success
        }
        
        self.current_memory.append(record)
        
        # 保持最多100条记录
        if len(self.current_memory) > 100:
            self.current_memory = self.current_memory[-100:]
        
        self.save_memory()
    
    def get_context_for_ai(self) -> str:
        """
        获取发送给 AI 的上下文
        
        Returns:
            格式化的历史操作上下文
        """
        if not self.current_memory:
            return ""
        
        # 取最近的 N 条记录
        recent = self.current_memory[-self.max_context_items:]
        
        context_lines = ["以下是此服务器的最近操作记录："]
        for i, record in enumerate(recent, 1):
            status = "✓" if record.get("success", True) else "✗"
            context_lines.append(
                f"{i}. [{record.get('time', '')}] {status} "
                f"用户说：「{record.get('input', '')}」 → 执行：{record.get('command', '')}"
            )
        
        return "\n".join(context_lines)
    
    def get_friendly_summary(self) -> str:
        """
        获取友好的记忆摘要（用于界面显示）
        
        Returns:
            摘要文本
        """
        if not self.current_memory:
            return "首次连接此服务器"
        
        count = len(self.current_memory)
        last = self.current_memory[-1]
        last_time = last.get("time", "未知")
        
        return f"已有 {count} 条操作记录，上次操作：{last_time}"
    
    def get_recent_commands(self, n: int = 5) -> List[str]:
        """获取最近执行的命令列表"""
        recent = self.current_memory[-n:] if self.current_memory else []
        return [r.get("command", "") for r in recent if r.get("command")]
    
    def search_history(self, keyword: str) -> List[Dict]:
        """
        搜索历史操作
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的记录列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for record in self.current_memory:
            if (keyword_lower in record.get("input", "").lower() or
                keyword_lower in record.get("command", "").lower()):
                results.append(record)
        
        return results
    
    def clear_memory(self, ip: str = None):
        """清空指定服务器的记忆"""
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

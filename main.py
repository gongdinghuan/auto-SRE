# -*- coding: utf-8 -*-
"""
自动运维助手 - 主程序入口 v2.0
支持多 AI 提供商、自动服务器检测、操作记忆
"""

from ssh_manager import SSHManager
from nlp_processor import NLPProcessor
from ai_providers import AIProviderManager
from memory_manager import MemoryManager
from gui import AutoOpsGUI


def main():
    """主程序入口"""
    # 初始化模块
    ssh_manager = SSHManager()
    nlp_processor = NLPProcessor()
    ai_manager = AIProviderManager()
    memory_manager = MemoryManager()
    
    # 创建并运行 GUI
    app = AutoOpsGUI(ssh_manager, nlp_processor, ai_manager, memory_manager)
    app.run()


if __name__ == "__main__":
    main()

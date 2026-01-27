# -*- coding: utf-8 -*-
"""
自动运维助手 - 主程序入口
通过 SSH 连接远程服务器，使用自然语言或 AI 执行运维命令
"""

from ssh_manager import SSHManager
from nlp_processor import NLPProcessor
from deepseek_ai import DeepSeekAI
from gui import AutoOpsGUI


def main():
    """主程序入口"""
    # 初始化模块
    ssh_manager = SSHManager()
    nlp_processor = NLPProcessor()
    deepseek_ai = DeepSeekAI()
    
    # 创建并运行 GUI
    app = AutoOpsGUI(ssh_manager, nlp_processor, deepseek_ai)
    app.run()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
自然语言处理模块
将用户的自然语言指令转换为 Linux 命令
"""

import re
from typing import Tuple, Optional


class NLPProcessor:
    """自然语言处理器"""
    
    def __init__(self):
        # 定义自然语言到命令的映射规则
        # 格式: (关键词列表, 对应命令, 描述)
        self.command_mappings = [
            # 系统信息
            (["磁盘", "硬盘", "存储空间", "磁盘空间"], "df -h", "查看磁盘使用情况"),
            (["内存", "内存使用", "ram"], "free -h", "查看内存使用情况"),
            (["cpu", "处理器", "cpu使用"], "top -bn1 | head -20", "查看 CPU 使用情况"),
            (["系统信息", "系统版本", "操作系统"], "uname -a && cat /etc/os-release", "查看系统信息"),
            (["运行时间", "开机时间", "uptime"], "uptime", "查看系统运行时间"),
            (["负载", "系统负载", "load"], "uptime && cat /proc/loadavg", "查看系统负载"),
            
            # 进程和服务
            (["进程", "进程列表", "运行进程"], "ps aux --sort=-%mem | head -20", "查看进程列表"),
            (["服务状态", "服务", "systemctl"], "systemctl list-units --type=service --state=running", "查看运行中的服务"),
            (["杀进程", "结束进程"], None, "需要指定进程名或 PID"),
            
            # 网络
            (["网络连接", "端口", "监听端口"], "netstat -tulpn 2>/dev/null || ss -tulpn", "查看网络连接"),
            (["ip地址", "网卡", "ip"], "ip addr show", "查看 IP 地址"),
            (["路由", "路由表"], "ip route show", "查看路由表"),
            (["网络测试", "ping"], None, "需要指定目标地址"),
            
            # 文件系统
            (["当前目录", "pwd"], "pwd", "显示当前目录"),
            (["列出文件", "文件列表", "ls", "目录内容"], "ls -la", "列出文件"),
            (["查看文件", "读取文件", "cat"], None, "需要指定文件路径"),
            (["文件大小", "目录大小"], "du -sh *", "查看文件/目录大小"),
            
            # 日志
            (["系统日志", "日志", "syslog"], "tail -n 50 /var/log/syslog 2>/dev/null || tail -n 50 /var/log/messages", "查看系统日志"),
            (["登录日志", "登录记录"], "last -n 20", "查看登录记录"),
            (["失败登录", "登录失败"], "lastb -n 20 2>/dev/null || echo '需要 root 权限'", "查看失败的登录尝试"),
            
            # 用户
            (["当前用户", "whoami"], "whoami", "显示当前用户"),
            (["在线用户", "登录用户", "who"], "who", "查看在线用户"),
            (["用户列表"], "cat /etc/passwd | cut -d: -f1", "查看所有用户"),
            
            # 系统操作
            (["重启", "重启服务器"], "sudo reboot", "重启服务器（需要确认）"),
            (["关机", "关闭服务器"], "sudo shutdown -h now", "关闭服务器（需要确认）"),
            (["更新系统", "系统更新", "apt update"], "sudo apt update && sudo apt upgrade -y", "更新系统"),
            
            # Docker
            (["docker容器", "容器列表", "docker ps"], "docker ps -a", "查看 Docker 容器"),
            (["docker镜像", "镜像列表"], "docker images", "查看 Docker 镜像"),
            
            # 帮助
            (["帮助", "help", "命令列表", "支持的命令"], None, "显示帮助信息"),
        ]
        
        # 危险命令列表（需要确认）
        self.dangerous_commands = [
            "reboot", "shutdown", "rm -rf", "mkfs", "dd if=", 
            ":(){ :|:& };:", "> /dev/sda", "chmod -R 777 /"
        ]
    
    def process(self, user_input: str) -> Tuple[str, str, bool]:
        """
        处理用户输入
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            (命令, 描述, 是否需要确认)
        """
        user_input = user_input.strip().lower()
        
        # 检查是否是帮助请求
        if any(keyword in user_input for keyword in ["帮助", "help", "命令列表", "支持的命令"]):
            return "", self._get_help_text(), False
        
        # 尝试匹配预定义的命令
        for keywords, command, description in self.command_mappings:
            if any(keyword in user_input for keyword in keywords):
                if command is None:
                    return "", f"[{description}]\n请提供更具体的指令或直接输入完整命令。", False
                
                needs_confirm = self._is_dangerous(command)
                return command, description, needs_confirm
        
        # 如果没有匹配的自然语言命令，检查是否是直接的 shell 命令
        if self._looks_like_command(user_input):
            needs_confirm = self._is_dangerous(user_input)
            return user_input, "直接执行命令", needs_confirm
        
        # 无法识别
        return "", f"无法识别的指令：'{user_input}'\n输入 '帮助' 查看支持的命令列表，或直接输入 Linux 命令。", False
    
    def _looks_like_command(self, text: str) -> bool:
        """判断输入是否看起来像 shell 命令"""
        # 常见命令开头
        command_starts = [
            "ls", "cd", "pwd", "cat", "grep", "find", "ps", "top", "df", "du",
            "free", "uname", "whoami", "who", "id", "sudo", "apt", "yum", "dnf",
            "systemctl", "service", "docker", "kubectl", "git", "npm", "pip",
            "python", "node", "java", "mysql", "mongo", "redis", "nginx",
            "curl", "wget", "ssh", "scp", "rsync", "tar", "zip", "unzip",
            "chmod", "chown", "cp", "mv", "rm", "mkdir", "touch", "vim", "nano",
            "head", "tail", "less", "more", "echo", "date", "cal", "history",
            "netstat", "ss", "ip", "ifconfig", "ping", "traceroute", "nslookup",
            "kill", "killall", "pkill", "htop", "iotop", "iftop"
        ]
        
        first_word = text.split()[0] if text.split() else ""
        return first_word in command_starts or text.startswith("./") or text.startswith("/")
    
    def _is_dangerous(self, command: str) -> bool:
        """检查命令是否危险"""
        command_lower = command.lower()
        return any(danger in command_lower for danger in self.dangerous_commands)
    
    def _get_help_text(self) -> str:
        """生成帮助文本"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    自动运维助手 - 命令帮助                      ║
╠══════════════════════════════════════════════════════════════╣
║  您可以使用自然语言描述操作，也可以直接输入 Linux 命令           ║
╠══════════════════════════════════════════════════════════════╣
║  【系统信息】                                                   ║
║    • 查看磁盘空间 / 查看内存 / 查看CPU使用                       ║
║    • 系统信息 / 运行时间 / 系统负载                              ║
╠══════════════════════════════════════════════════════════════╣
║  【进程和服务】                                                 ║
║    • 查看进程 / 服务状态                                        ║
╠══════════════════════════════════════════════════════════════╣
║  【网络】                                                       ║
║    • 网络连接 / 查看端口 / IP地址 / 路由表                       ║
╠══════════════════════════════════════════════════════════════╣
║  【文件系统】                                                   ║
║    • 当前目录 / 列出文件 / 文件大小                              ║
╠══════════════════════════════════════════════════════════════╣
║  【日志】                                                       ║
║    • 系统日志 / 登录日志 / 失败登录                              ║
╠══════════════════════════════════════════════════════════════╣
║  【用户】                                                       ║
║    • 当前用户 / 在线用户 / 用户列表                              ║
╠══════════════════════════════════════════════════════════════╣
║  【Docker】                                                     ║
║    • Docker容器 / Docker镜像                                    ║
╠══════════════════════════════════════════════════════════════╣
║  【系统操作】⚠️ 危险操作会要求确认                               ║
║    • 重启服务器 / 关机 / 更新系统                                ║
╚══════════════════════════════════════════════════════════════╝
"""
        return help_text

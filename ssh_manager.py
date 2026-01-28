# -*- coding: utf-8 -*-
"""
SSH 连接管理模块
用于处理与远程服务器的 SSH 连接和命令执行
支持自动检测服务器信息

作者: GDH
"""

import paramiko
from typing import Tuple, Optional, Dict


class SSHManager:
    """SSH 连接管理器"""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.connected: bool = False
        self.host: str = ""
        self.port: int = 22
        self.username: str = ""
        
        # 服务器信息
        self.server_info: Dict[str, str] = {}
        self.detected_os: str = "Linux"
    
    def connect(self, host: str, port: int, username: str, password: str) -> Tuple[bool, str]:
        """
        建立 SSH 连接
        
        Args:
            host: 服务器 IP 地址
            port: SSH 端口号
            username: 用户名
            password: 密码
            
        Returns:
            (成功状态, 消息)
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10
            )
            
            self.connected = True
            self.host = host
            self.port = port
            self.username = username
            
            # 自动检测服务器信息
            self._detect_server_info()
            
            return True, f"成功连接到 {username}@{host}:{port}"
            
        except paramiko.AuthenticationException:
            return False, "认证失败：用户名或密码错误"
        except paramiko.SSHException as e:
            return False, f"SSH 连接错误：{str(e)}"
        except TimeoutError:
            return False, "连接超时：无法连接到服务器"
        except Exception as e:
            return False, f"连接错误：{str(e)}"
    
    def _detect_server_info(self):
        """自动检测服务器信息"""
        self.server_info = {}
        self.detected_os = "Linux"
        
        if not self.connected or not self.client:
            return
        
        try:
            # 检测 OS 版本
            _, stdout, _ = self.client.exec_command(
                "cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null || uname -a",
                timeout=5
            )
            os_info = stdout.read().decode('utf-8', errors='replace').strip()
            self.server_info['os_release'] = os_info
            
            # 解析操作系统类型
            os_lower = os_info.lower()
            if 'ubuntu' in os_lower:
                self.detected_os = "Ubuntu"
            elif 'debian' in os_lower:
                self.detected_os = "Debian"
            elif 'centos' in os_lower:
                self.detected_os = "CentOS"
            elif 'red hat' in os_lower or 'rhel' in os_lower:
                self.detected_os = "RHEL"
            elif 'fedora' in os_lower:
                self.detected_os = "Fedora"
            elif 'alpine' in os_lower:
                self.detected_os = "Alpine"
            elif 'arch' in os_lower:
                self.detected_os = "Arch"
            elif 'opensuse' in os_lower or 'suse' in os_lower:
                self.detected_os = "openSUSE"
            else:
                self.detected_os = "Linux"
            
            # 检测内核版本
            _, stdout, _ = self.client.exec_command("uname -r", timeout=5)
            self.server_info['kernel'] = stdout.read().decode('utf-8', errors='replace').strip()
            
            # 检测 CPU 信息
            _, stdout, _ = self.client.exec_command(
                "grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2",
                timeout=5
            )
            cpu_info = stdout.read().decode('utf-8', errors='replace').strip()
            if cpu_info:
                self.server_info['cpu'] = cpu_info
            
            # 检测内存
            _, stdout, _ = self.client.exec_command(
                "free -h | grep Mem | awk '{print $2}'",
                timeout=5
            )
            mem_info = stdout.read().decode('utf-8', errors='replace').strip()
            if mem_info:
                self.server_info['memory'] = mem_info
            
            # 检测主机名
            _, stdout, _ = self.client.exec_command("hostname", timeout=5)
            self.server_info['hostname'] = stdout.read().decode('utf-8', errors='replace').strip()
            
        except Exception as e:
            print(f"检测服务器信息失败: {e}")
    
    def get_server_info_summary(self) -> str:
        """获取服务器信息摘要"""
        if not self.server_info:
            return "未检测到服务器信息"
        
        lines = []
        if 'hostname' in self.server_info:
            lines.append(f"主机名: {self.server_info['hostname']}")
        lines.append(f"操作系统: {self.detected_os}")
        if 'kernel' in self.server_info:
            lines.append(f"内核: {self.server_info['kernel']}")
        if 'cpu' in self.server_info:
            lines.append(f"CPU: {self.server_info['cpu']}")
        if 'memory' in self.server_info:
            lines.append(f"内存: {self.server_info['memory']}")
        
        return "\n".join(lines)
    
    def get_detected_os(self) -> str:
        """获取检测到的操作系统类型"""
        return self.detected_os
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """
        执行远程命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            (成功状态, 输出结果)
        """
        if not self.connected or self.client is None:
            return False, "错误：未连接到服务器"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            
            if error and not output:
                return False, f"命令执行错误：\n{error}"
            elif error:
                return True, f"{output}\n[警告] {error}"
            else:
                return True, output if output else "命令执行成功（无输出）"
                
        except Exception as e:
            return False, f"命令执行失败：{str(e)}"
    
    def disconnect(self) -> str:
        """断开 SSH 连接"""
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        self.client = None
        self.connected = False
        host = self.host
        self.host = ""
        self.username = ""
        self.server_info = {}
        self.detected_os = "Linux"
        
        return f"已断开与 {host} 的连接"
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_connection_info(self) -> str:
        """获取当前连接信息"""
        if self.connected:
            return f"{self.username}@{self.host}:{self.port}"
        return "未连接"
    
    def get_host(self) -> str:
        """获取当前连接的主机 IP"""
        return self.host

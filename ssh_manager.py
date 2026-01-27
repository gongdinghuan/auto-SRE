# -*- coding: utf-8 -*-
"""
SSH 连接管理模块
用于处理与远程服务器的 SSH 连接和命令执行
"""

import paramiko
from typing import Tuple, Optional


class SSHManager:
    """SSH 连接管理器"""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.connected: bool = False
        self.host: str = ""
        self.port: int = 22
        self.username: str = ""
    
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
            
            return True, f"成功连接到 {username}@{host}:{port}"
            
        except paramiko.AuthenticationException:
            return False, "认证失败：用户名或密码错误"
        except paramiko.SSHException as e:
            return False, f"SSH 连接错误：{str(e)}"
        except TimeoutError:
            return False, "连接超时：无法连接到服务器"
        except Exception as e:
            return False, f"连接错误：{str(e)}"
    
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
        
        return f"已断开与 {host} 的连接"
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_connection_info(self) -> str:
        """获取当前连接信息"""
        if self.connected:
            return f"{self.username}@{self.host}:{self.port}"
        return "未连接"

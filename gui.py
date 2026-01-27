# -*- coding: utf-8 -*-
"""
图形用户界面模块
提供用户友好的操作界面，集成 DeepSeek AI
支持可折叠面板，最大化输出区域
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Callable, Optional
import threading


class CollapsibleFrame(tk.Frame):
    """可折叠的面板"""
    
    def __init__(self, parent, title="", bg='#16213e', fg='#00d4ff', **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        
        self.is_expanded = True
        self.title = title
        self.bg = bg
        self.fg = fg
        
        # 标题栏
        self.header = tk.Frame(self, bg=bg)
        self.header.pack(fill=tk.X)
        
        # 折叠按钮
        self.toggle_btn = tk.Label(
            self.header,
            text="▼",
            font=('Consolas', 10, 'bold'),
            bg=bg,
            fg=fg,
            cursor='hand2',
            padx=5
        )
        self.toggle_btn.pack(side=tk.LEFT)
        self.toggle_btn.bind('<Button-1>', self._toggle)
        
        # 标题
        self.title_label = tk.Label(
            self.header,
            text=title,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg=bg,
            fg=fg,
            cursor='hand2'
        )
        self.title_label.pack(side=tk.LEFT, padx=(5, 0))
        self.title_label.bind('<Button-1>', self._toggle)
        
        # 可选的状态标签
        self.status_label = tk.Label(
            self.header,
            text="",
            font=('Microsoft YaHei UI', 9),
            bg=bg,
            fg='#888'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 内容区域
        self.content = tk.Frame(self, bg=bg, padx=15, pady=10)
        self.content.pack(fill=tk.X)
    
    def _toggle(self, event=None):
        """切换展开/折叠状态"""
        if self.is_expanded:
            self.content.pack_forget()
            self.toggle_btn.config(text="▶")
            self.is_expanded = False
        else:
            self.content.pack(fill=tk.X)
            self.toggle_btn.config(text="▼")
            self.is_expanded = True
    
    def collapse(self):
        """折叠"""
        if self.is_expanded:
            self._toggle()
    
    def expand(self):
        """展开"""
        if not self.is_expanded:
            self._toggle()
    
    def set_status(self, text, color='#888'):
        """设置状态文本"""
        self.status_label.config(text=text, fg=color)


class AutoOpsGUI:
    """自动运维 GUI 应用"""
    
    def __init__(self, ssh_manager, nlp_processor, deepseek_ai=None):
        self.ssh_manager = ssh_manager
        self.nlp_processor = nlp_processor
        self.deepseek_ai = deepseek_ai
        
        # 创建主窗口 (必须先创建 root)
        self.root = tk.Tk()
        self.root.title("🖥️ 自动运维助手 - SSH 远程管理工具 (AI 增强版)")
        self.root.geometry("950x800")
        self.root.minsize(850, 600)
        
        # AI 模式开关 (必须在 root 创建后初始化)
        self.ai_mode_enabled = tk.BooleanVar(value=False)
        
        # 设置样式
        self._setup_styles()
        
        # 创建界面组件
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
        # 状态
        self.pending_confirm_command = None
    
    def _setup_styles(self):
        """设置界面样式"""
        self.root.configure(bg='#1a1a2e')
        
        style = ttk.Style()
        style.theme_use('clam')
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = tk.Frame(self.root, bg='#1a1a2e', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== 标题栏 ==========
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, 
                              text="🖥️ 自动运维助手",
                              font=('Microsoft YaHei UI', 16, 'bold'),
                              bg='#1a1a2e',
                              fg='#00d4ff')
        title_label.pack(side=tk.LEFT)
        
        # 快捷折叠按钮
        collapse_all_btn = tk.Button(title_frame, text="📁 全部折叠",
                                    font=('Microsoft YaHei UI', 9),
                                    bg='#2d3a4f', fg='#ddd',
                                    activebackground='#3d4a5f',
                                    relief=tk.FLAT, padx=10, pady=2,
                                    cursor='hand2',
                                    command=self._collapse_all)
        collapse_all_btn.pack(side=tk.RIGHT, padx=5)
        
        expand_all_btn = tk.Button(title_frame, text="📂 全部展开",
                                  font=('Microsoft YaHei UI', 9),
                                  bg='#2d3a4f', fg='#ddd',
                                  activebackground='#3d4a5f',
                                  relief=tk.FLAT, padx=10, pady=2,
                                  cursor='hand2',
                                  command=self._expand_all)
        expand_all_btn.pack(side=tk.RIGHT, padx=5)
        
        # ========== AI 配置区域（可折叠）==========
        self.ai_panel = CollapsibleFrame(main_frame, title="🤖 DeepSeek AI 配置", bg='#1e3a5f')
        self.ai_panel.pack(fill=tk.X, pady=(0, 8))
        
        ai_row = tk.Frame(self.ai_panel.content, bg='#1e3a5f')
        ai_row.pack(fill=tk.X)
        
        # AI 开关
        self.ai_switch = tk.Checkbutton(ai_row, 
                                        text="启用 AI 解析",
                                        variable=self.ai_mode_enabled,
                                        font=('Microsoft YaHei UI', 10, 'bold'),
                                        bg='#1e3a5f', fg='#00ff88',
                                        selectcolor='#0f0f23',
                                        activebackground='#1e3a5f',
                                        activeforeground='#00ff88',
                                        command=self._on_ai_toggle)
        self.ai_switch.pack(side=tk.LEFT)
        
        # 设置 API Key 按钮
        self.api_key_btn = tk.Button(ai_row, text="🔑 设置 API Key",
                                    font=('Microsoft YaHei UI', 9),
                                    bg='#4a5568', fg='#fff',
                                    activebackground='#5a6578',
                                    relief=tk.FLAT, padx=12, pady=4,
                                    cursor='hand2',
                                    command=self._set_api_key)
        self.api_key_btn.pack(side=tk.RIGHT)
        
        self.ai_panel.set_status("● 未配置 API Key", '#ff4444')
        
        # ========== 连接配置区域（可折叠）==========
        self.conn_panel = CollapsibleFrame(main_frame, title="🔗 服务器连接", bg='#16213e')
        self.conn_panel.pack(fill=tk.X, pady=(0, 8))
        
        # 第一行：IP、端口、用户名、密码（紧凑布局）
        row1 = tk.Frame(self.conn_panel.content, bg='#16213e')
        row1.pack(fill=tk.X, pady=3)
        
        tk.Label(row1, text="IP:", font=('Microsoft YaHei UI', 9),
                bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
        
        self.ip_entry = tk.Entry(row1, font=('Consolas', 10), width=15,
                                bg='#0f0f23', fg='#fff', insertbackground='white',
                                relief=tk.FLAT, highlightthickness=1,
                                highlightcolor='#00d4ff', highlightbackground='#333')
        self.ip_entry.pack(side=tk.LEFT, padx=(3, 10))
        self.ip_entry.insert(0, "192.168.1.1")
        
        tk.Label(row1, text="端口:", font=('Microsoft YaHei UI', 9),
                bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
        
        self.port_entry = tk.Entry(row1, font=('Consolas', 10), width=6,
                                  bg='#0f0f23', fg='#fff', insertbackground='white',
                                  relief=tk.FLAT, highlightthickness=1,
                                  highlightcolor='#00d4ff', highlightbackground='#333')
        self.port_entry.pack(side=tk.LEFT, padx=(3, 10))
        self.port_entry.insert(0, "22")
        
        tk.Label(row1, text="用户:", font=('Microsoft YaHei UI', 9),
                bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
        
        self.user_entry = tk.Entry(row1, font=('Consolas', 10), width=12,
                                  bg='#0f0f23', fg='#fff', insertbackground='white',
                                  relief=tk.FLAT, highlightthickness=1,
                                  highlightcolor='#00d4ff', highlightbackground='#333')
        self.user_entry.pack(side=tk.LEFT, padx=(3, 10))
        self.user_entry.insert(0, "root")
        
        tk.Label(row1, text="密码:", font=('Microsoft YaHei UI', 9),
                bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
        
        self.pass_entry = tk.Entry(row1, font=('Consolas', 10), width=15,
                                  bg='#0f0f23', fg='#fff', insertbackground='white',
                                  relief=tk.FLAT, show='●', highlightthickness=1,
                                  highlightcolor='#00d4ff', highlightbackground='#333')
        self.pass_entry.pack(side=tk.LEFT, padx=(3, 0))
        
        # 连接按钮行
        btn_row = tk.Frame(self.conn_panel.content, bg='#16213e')
        btn_row.pack(fill=tk.X, pady=(8, 0))
        
        self.connect_btn = tk.Button(btn_row, text="🔌 连接",
                                    font=('Microsoft YaHei UI', 9, 'bold'),
                                    bg='#00d4ff', fg='#000',
                                    activebackground='#00a8cc',
                                    relief=tk.FLAT, padx=15, pady=5,
                                    cursor='hand2',
                                    command=self._on_connect)
        self.connect_btn.pack(side=tk.LEFT)
        
        self.disconnect_btn = tk.Button(btn_row, text="❌ 断开",
                                       font=('Microsoft YaHei UI', 9),
                                       bg='#e94560', fg='#fff',
                                       activebackground='#c73e54',
                                       relief=tk.FLAT, padx=15, pady=5,
                                       cursor='hand2',
                                       command=self._on_disconnect,
                                       state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        self.conn_panel.set_status("● 未连接", '#ff4444')
        
        # ========== 命令输入区域（可折叠）==========
        self.cmd_panel = CollapsibleFrame(main_frame, title="💬 命令输入", bg='#16213e')
        self.cmd_panel.pack(fill=tk.X, pady=(0, 8))
        
        # 输入行
        input_row = tk.Frame(self.cmd_panel.content, bg='#16213e')
        input_row.pack(fill=tk.X)
        
        self.cmd_entry = tk.Entry(input_row, font=('Microsoft YaHei UI', 11),
                                 bg='#0f0f23', fg='#fff', insertbackground='white',
                                 relief=tk.FLAT, highlightthickness=2,
                                 highlightcolor='#00d4ff', highlightbackground='#333')
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        
        self.exec_btn = tk.Button(input_row, text="▶ 执行",
                                 font=('Microsoft YaHei UI', 10, 'bold'),
                                 bg='#00ff88', fg='#000',
                                 activebackground='#00cc6a',
                                 relief=tk.FLAT, padx=20, pady=6,
                                 cursor='hand2',
                                 command=self._on_execute,
                                 state=tk.DISABLED)
        self.exec_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        # 快捷命令按钮
        quick_frame = tk.Frame(self.cmd_panel.content, bg='#16213e')
        quick_frame.pack(fill=tk.X, pady=(8, 0))
        
        quick_commands = [
            ("📊 磁盘", "查看磁盘空间"),
            ("🧠 内存", "查看内存"),
            ("⚡ CPU", "查看CPU"),
            ("📋 进程", "查看进程"),
            ("🌐 网络", "网络连接"),
            ("📜 日志", "系统日志"),
            ("❓ 帮助", "帮助"),
        ]
        
        for text, cmd in quick_commands:
            btn = tk.Button(quick_frame, text=text,
                           font=('Microsoft YaHei UI', 8),
                           bg='#2d3a4f', fg='#ddd',
                           activebackground='#3d4a5f',
                           relief=tk.FLAT, padx=8, pady=2,
                           cursor='hand2',
                           command=lambda c=cmd: self._quick_command(c))
            btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # ========== 输出区域（始终可见，占据剩余空间）==========
        output_frame = tk.LabelFrame(main_frame,
                                    text=" 📺 输出结果 ",
                                    font=('Microsoft YaHei UI', 10, 'bold'),
                                    bg='#16213e',
                                    fg='#00d4ff',
                                    padx=10,
                                    pady=8)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输出文本框
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=('Consolas', 10),
            bg='#0f0f23',
            fg='#00ff88',
            insertbackground='white',
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置标签样式
        self.output_text.tag_config('info', foreground='#00d4ff')
        self.output_text.tag_config('success', foreground='#00ff88')
        self.output_text.tag_config('error', foreground='#ff4444')
        self.output_text.tag_config('warning', foreground='#ffaa00')
        self.output_text.tag_config('command', foreground='#ff79c6')
        self.output_text.tag_config('help', foreground='#bd93f9')
        self.output_text.tag_config('ai', foreground='#f1c40f')
        
        # 底部工具栏
        toolbar = tk.Frame(output_frame, bg='#16213e')
        toolbar.pack(fill=tk.X, pady=(8, 0))
        
        clear_btn = tk.Button(toolbar, text="🗑️ 清空",
                             font=('Microsoft YaHei UI', 8),
                             bg='#2d3a4f', fg='#ddd',
                             activebackground='#3d4a5f',
                             relief=tk.FLAT, padx=10, pady=2,
                             cursor='hand2',
                             command=self._clear_output)
        clear_btn.pack(side=tk.RIGHT)
        
        # 提示信息
        self.hint_label = tk.Label(toolbar,
                                  text="💡 使用自然语言或直接输入命令 | 点击面板标题可折叠/展开",
                                  font=('Microsoft YaHei UI', 8),
                                  bg='#16213e', fg='#666')
        self.hint_label.pack(side=tk.LEFT)
        
        # 初始欢迎信息
        self._append_output("╔═══════════════════════════════════════════════════════════════════╗\n", 'info')
        self._append_output("║          欢迎使用自动运维助手 🖥️ (AI 增强版)                       ║\n", 'info')
        self._append_output("╠═══════════════════════════════════════════════════════════════════╣\n", 'info')
        self._append_output("║  💡 点击各区域标题可折叠/展开，最大化输出显示区域                   ║\n", 'info')
        self._append_output("║  1. 设置 API Key 并启用 AI → 2. 连接服务器 → 3. 输入命令          ║\n", 'info')
        self._append_output("╚═══════════════════════════════════════════════════════════════════╝\n\n", 'info')
    
    def _collapse_all(self):
        """折叠所有面板"""
        self.ai_panel.collapse()
        self.conn_panel.collapse()
        self.cmd_panel.collapse()
    
    def _expand_all(self):
        """展开所有面板"""
        self.ai_panel.expand()
        self.conn_panel.expand()
        self.cmd_panel.expand()
    
    def _bind_events(self):
        """绑定事件"""
        self.cmd_entry.bind('<Return>', lambda e: self._on_execute())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _set_api_key(self):
        """设置 DeepSeek API Key"""
        api_key = simpledialog.askstring(
            "设置 DeepSeek API Key",
            "请输入您的 DeepSeek API Key:\n\n(可从 https://platform.deepseek.com 获取)",
            show='*'
        )
        
        if api_key:
            if self.deepseek_ai and self.deepseek_ai.set_api_key(api_key):
                self.ai_panel.set_status("● 已配置", '#00ff88')
                self._append_output("[AI] DeepSeek API Key 配置成功！\n\n", 'ai')
            else:
                messagebox.showerror("错误", "API Key 设置失败")
    
    def _on_ai_toggle(self):
        """AI 模式开关"""
        if self.ai_mode_enabled.get():
            if not self.deepseek_ai or not self.deepseek_ai.is_configured():
                messagebox.showwarning("提示", "请先设置 DeepSeek API Key")
                self.ai_mode_enabled.set(False)
                return
            self._append_output("[AI] AI 模式已启用\n\n", 'ai')
            self.ai_panel.set_status("● AI 已启用", '#00ff88')
        else:
            self._append_output("[AI] AI 模式已关闭\n\n", 'info')
            if self.deepseek_ai and self.deepseek_ai.is_configured():
                self.ai_panel.set_status("● 已配置", '#00ff88')
            else:
                self.ai_panel.set_status("● 未配置", '#ff4444')
    
    def _on_connect(self):
        """连接按钮点击事件"""
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        
        if not ip:
            messagebox.showerror("错误", "请输入服务器 IP 地址")
            return
        
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字")
            return
        
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return
        
        self.connect_btn.config(state=tk.DISABLED, text="连接中...")
        self._append_output(f"[INFO] 正在连接到 {username}@{ip}:{port}...\n", 'info')
        
        def connect_thread():
            success, message = self.ssh_manager.connect(ip, port, username, password)
            self.root.after(0, lambda: self._on_connect_result(success, message))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_connect_result(self, success: bool, message: str):
        """处理连接结果"""
        if success:
            self._append_output(f"[SUCCESS] {message}\n\n", 'success')
            self.conn_panel.set_status(f"● {self.ssh_manager.get_connection_info()}", '#00ff88')
            self.connect_btn.config(state=tk.DISABLED, text="✓ 已连接")
            self.disconnect_btn.config(state=tk.NORMAL)
            self.exec_btn.config(state=tk.NORMAL)
            
            # 禁用输入框
            self.ip_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            self.user_entry.config(state=tk.DISABLED)
            self.pass_entry.config(state=tk.DISABLED)
            
            # 自动折叠连接面板
            self.conn_panel.collapse()
        else:
            self._append_output(f"[ERROR] {message}\n\n", 'error')
            self.connect_btn.config(state=tk.NORMAL, text="🔌 连接")
    
    def _on_disconnect(self):
        """断开连接"""
        message = self.ssh_manager.disconnect()
        self._append_output(f"[INFO] {message}\n\n", 'info')
        
        self.conn_panel.set_status("● 未连接", '#ff4444')
        self.connect_btn.config(state=tk.NORMAL, text="🔌 连接")
        self.disconnect_btn.config(state=tk.DISABLED)
        self.exec_btn.config(state=tk.DISABLED)
        
        self.ip_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.user_entry.config(state=tk.NORMAL)
        self.pass_entry.config(state=tk.NORMAL)
        
        self.conn_panel.expand()
    
    def _on_execute(self):
        """执行命令"""
        user_input = self.cmd_entry.get().strip()
        if not user_input:
            return
        
        self.cmd_entry.delete(0, tk.END)
        self._append_output(f">>> {user_input}\n", 'command')
        
        if self.ai_mode_enabled.get() and self.deepseek_ai and self.deepseek_ai.is_configured():
            self._process_with_ai(user_input)
        else:
            self._process_with_local(user_input)
    
    def _process_with_ai(self, user_input: str):
        """使用 AI 处理用户输入"""
        self._append_output("[AI] 正在分析...\n", 'ai')
        self.exec_btn.config(state=tk.DISABLED)
        
        def ai_thread():
            command, description, dangerous, explanation = self.deepseek_ai.parse_command(user_input)
            self.root.after(0, lambda: self._on_ai_result(command, description, dangerous, explanation))
        
        threading.Thread(target=ai_thread, daemon=True).start()
    
    def _on_ai_result(self, command: str, description: str, dangerous: bool, explanation: str):
        """处理 AI 解析结果"""
        self.exec_btn.config(state=tk.NORMAL)
        
        if not command:
            self._append_output(f"[AI] {description}\n", 'warning')
            self._append_output(f"     {explanation}\n\n", 'info')
            return
        
        self._append_output(f"[AI] {description}\n", 'ai')
        self._append_output(f"[命令] {command}\n", 'info')
        
        if dangerous:
            if messagebox.askyesno("⚠️ 危险操作", f"命令: {command}\n\n{explanation}\n\n确定执行？"):
                self._execute_command(command)
            else:
                self._append_output("[取消]\n\n", 'warning')
        else:
            self._execute_command(command)
    
    def _process_with_local(self, user_input: str):
        """使用本地规则处理用户输入"""
        command, description, needs_confirm = self.nlp_processor.process(user_input)
        
        if not command:
            self._append_output(f"{description}\n\n", 'help' if "帮助" in description else 'warning')
            return
        
        self._append_output(f"[解析] {description}\n", 'info')
        self._append_output(f"[命令] {command}\n", 'info')
        
        if needs_confirm:
            if messagebox.askyesno("危险操作", f"命令: {command}\n\n确定执行？"):
                self._execute_command(command)
            else:
                self._append_output("[取消]\n\n", 'warning')
        else:
            self._execute_command(command)
    
    def _execute_command(self, command: str):
        """执行 SSH 命令"""
        self._append_output("[执行中...]\n", 'info')
        self.exec_btn.config(state=tk.DISABLED)
        
        def execute_thread():
            success, output = self.ssh_manager.execute_command(command)
            self.root.after(0, lambda: self._on_execute_result(success, output))
        
        threading.Thread(target=execute_thread, daemon=True).start()
    
    def _on_execute_result(self, success: bool, output: str):
        """处理命令执行结果"""
        if success:
            self._append_output(f"{output}\n", 'success')
        else:
            self._append_output(f"{output}\n", 'error')
        
        self._append_output("\n", 'info')
        self.exec_btn.config(state=tk.NORMAL)
    
    def _quick_command(self, command: str):
        """快捷命令"""
        if not self.ssh_manager.is_connected():
            messagebox.showwarning("提示", "请先连接服务器")
            return
        
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, command)
        self._on_execute()
    
    def _append_output(self, text: str, tag: str = None):
        """添加输出文本"""
        self.output_text.config(state=tk.NORMAL)
        if tag:
            self.output_text.insert(tk.END, text, tag)
        else:
            self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def _clear_output(self):
        """清空输出"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def _on_close(self):
        """关闭窗口"""
        if self.ssh_manager.is_connected():
            if messagebox.askyesno("确认退出", "SSH 连接仍在，确定退出？"):
                self.ssh_manager.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

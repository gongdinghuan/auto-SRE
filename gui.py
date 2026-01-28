# -*- coding: utf-8 -*-
"""
图形用户界面模块
集成多 AI 提供商、服务器信息显示、操作记忆功能

作者: GDH
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Optional
import threading


class CollapsibleFrame(tk.Frame):
    """可折叠的面板"""
    
    def __init__(self, parent, title="", bg='#16213e', fg='#00d4ff', **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        
        self.is_expanded = True
        self.bg = bg
        
        self.header = tk.Frame(self, bg=bg)
        self.header.pack(fill=tk.X)
        
        self.toggle_btn = tk.Label(self.header, text="▼", font=('Consolas', 10, 'bold'),
                                   bg=bg, fg=fg, cursor='hand2', padx=5)
        self.toggle_btn.pack(side=tk.LEFT)
        self.toggle_btn.bind('<Button-1>', self._toggle)
        
        self.title_label = tk.Label(self.header, text=title, font=('Microsoft YaHei UI', 10, 'bold'),
                                    bg=bg, fg=fg, cursor='hand2')
        self.title_label.pack(side=tk.LEFT, padx=(5, 0))
        self.title_label.bind('<Button-1>', self._toggle)
        
        self.status_label = tk.Label(self.header, text="", font=('Microsoft YaHei UI', 9),
                                     bg=bg, fg='#888')
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        self.content = tk.Frame(self, bg=bg, padx=15, pady=10)
        self.content.pack(fill=tk.X)
    
    def _toggle(self, event=None):
        if self.is_expanded:
            self.content.pack_forget()
            self.toggle_btn.config(text="▶")
            self.is_expanded = False
        else:
            self.content.pack(fill=tk.X)
            self.toggle_btn.config(text="▼")
            self.is_expanded = True
    
    def collapse(self):
        if self.is_expanded: self._toggle()
    
    def expand(self):
        if not self.is_expanded: self._toggle()
    
    def set_status(self, text, color='#888'):
        self.status_label.config(text=text, fg=color)


class AutoOpsGUI:
    """自动运维 GUI 应用"""
    
    def __init__(self, ssh_manager, nlp_processor, ai_provider_manager, memory_manager):
        self.ssh_manager = ssh_manager
        self.nlp_processor = nlp_processor
        self.ai_manager = ai_provider_manager
        self.memory_manager = memory_manager
        
        self.root = tk.Tk()
        self.root.title("🖥️ 自动运维助手 - AI 增强版gdh v2.0")
        self.root.geometry("1000x850")
        self.root.minsize(900, 700)
        
        self.ai_mode_enabled = tk.BooleanVar(value=False)
        self.current_provider = tk.StringVar(value="DeepSeek")
        
        self._setup_styles()
        self._create_widgets()
        self._bind_events()
        
        # 保存用户输入用于记忆
        self.last_user_input = ""
    
    def _setup_styles(self):
        self.root.configure(bg='#1a1a2e')
        style = ttk.Style()
        style.theme_use('clam')
    
    def _create_widgets(self):
        main_frame = tk.Frame(self.root, bg='#1a1a2e', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="🖥️ 自动运维助手 v2.0",
                font=('Microsoft YaHei UI', 16, 'bold'), bg='#1a1a2e', fg='#00d4ff').pack(side=tk.LEFT)
        
        tk.Button(title_frame, text="📁 全部折叠", font=('Microsoft YaHei UI', 9),
                 bg='#2d3a4f', fg='#ddd', relief=tk.FLAT, padx=10, pady=2,
                 command=self._collapse_all).pack(side=tk.RIGHT, padx=5)
        tk.Button(title_frame, text="📂 全部展开", font=('Microsoft YaHei UI', 9),
                 bg='#2d3a4f', fg='#ddd', relief=tk.FLAT, padx=10, pady=2,
                 command=self._expand_all).pack(side=tk.RIGHT, padx=5)
        
        # ========== AI 配置 ==========
        self.ai_panel = CollapsibleFrame(main_frame, title="🤖 AI 配置", bg='#1e3a5f')
        self.ai_panel.pack(fill=tk.X, pady=(0, 8))
        
        ai_row1 = tk.Frame(self.ai_panel.content, bg='#1e3a5f')
        ai_row1.pack(fill=tk.X, pady=3)
        
        self.ai_switch = tk.Checkbutton(ai_row1, text="启用 AI", variable=self.ai_mode_enabled,
                                        font=('Microsoft YaHei UI', 10, 'bold'),
                                        bg='#1e3a5f', fg='#00ff88', selectcolor='#0f0f23',
                                        command=self._on_ai_toggle)
        self.ai_switch.pack(side=tk.LEFT)
        
        tk.Label(ai_row1, text="选择提供商:", font=('Microsoft YaHei UI', 9),
                bg='#1e3a5f', fg='#ddd').pack(side=tk.LEFT, padx=(20, 5))
        
        self.provider_combo = ttk.Combobox(ai_row1, textvariable=self.current_provider,
                                          values=self.ai_manager.get_provider_names(),
                                          state='readonly', width=12)
        self.provider_combo.pack(side=tk.LEFT)
        
        tk.Button(ai_row1, text="🔑 设置 API Key", font=('Microsoft YaHei UI', 9),
                 bg='#4a5568', fg='#fff', relief=tk.FLAT, padx=12, pady=4,
                 command=self._set_api_key).pack(side=tk.LEFT, padx=(15, 0))
        
        tk.Button(ai_row1, text="⚙️ 设置模型", font=('Microsoft YaHei UI', 9),
                 bg='#4a5568', fg='#fff', relief=tk.FLAT, padx=12, pady=4,
                 command=self._set_model).pack(side=tk.LEFT, padx=(8, 0))
        
        self.ai_panel.set_status("● 未配置", '#ff4444')
        
        # ========== 服务器连接 ==========
        self.conn_panel = CollapsibleFrame(main_frame, title="🔗 服务器连接", bg='#16213e')
        self.conn_panel.pack(fill=tk.X, pady=(0, 8))
        
        conn_row = tk.Frame(self.conn_panel.content, bg='#16213e')
        conn_row.pack(fill=tk.X, pady=3)
        
        for label, width, default, attr in [
            ("IP:", 15, "192.168.1.1", "ip_entry"),
            ("端口:", 6, "22", "port_entry"),
            ("用户:", 12, "root", "user_entry")
        ]:
            tk.Label(conn_row, text=label, font=('Microsoft YaHei UI', 9),
                    bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
            entry = tk.Entry(conn_row, font=('Consolas', 10), width=width,
                           bg='#0f0f23', fg='#fff', insertbackground='white',
                           relief=tk.FLAT, highlightthickness=1,
                           highlightcolor='#00d4ff', highlightbackground='#333')
            entry.pack(side=tk.LEFT, padx=(3, 10))
            entry.insert(0, default)
            setattr(self, attr, entry)
        
        tk.Label(conn_row, text="密码:", font=('Microsoft YaHei UI', 9),
                bg='#16213e', fg='#ddd').pack(side=tk.LEFT)
        self.pass_entry = tk.Entry(conn_row, font=('Consolas', 10), width=15,
                                  bg='#0f0f23', fg='#fff', insertbackground='white',
                                  relief=tk.FLAT, show='●', highlightthickness=1,
                                  highlightcolor='#00d4ff', highlightbackground='#333')
        self.pass_entry.pack(side=tk.LEFT, padx=(3, 0))
        
        btn_row = tk.Frame(self.conn_panel.content, bg='#16213e')
        btn_row.pack(fill=tk.X, pady=(8, 0))
        
        self.connect_btn = tk.Button(btn_row, text="🔌 连接", font=('Microsoft YaHei UI', 9, 'bold'),
                                    bg='#00d4ff', fg='#000', relief=tk.FLAT, padx=15, pady=5,
                                    command=self._on_connect)
        self.connect_btn.pack(side=tk.LEFT)
        
        self.disconnect_btn = tk.Button(btn_row, text="❌ 断开", font=('Microsoft YaHei UI', 9),
                                       bg='#e94560', fg='#fff', relief=tk.FLAT, padx=15, pady=5,
                                       command=self._on_disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        self.conn_panel.set_status("● 未连接", '#ff4444')
        
        # ========== 服务器信息 (连接后显示) ==========
        self.info_panel = CollapsibleFrame(main_frame, title="📊 服务器信息", bg='#1a3a1a')
        self.info_panel.pack(fill=tk.X, pady=(0, 8))
        self.info_panel.collapse()  # 初始折叠
        
        self.server_info_label = tk.Label(self.info_panel.content, text="连接服务器后显示",
                                         font=('Consolas', 9), bg='#1a3a1a', fg='#00ff88',
                                         justify=tk.LEFT, anchor='w')
        self.server_info_label.pack(fill=tk.X)
        
        self.memory_status_label = tk.Label(self.info_panel.content, text="",
                                           font=('Microsoft YaHei UI', 9), bg='#1a3a1a', fg='#888')
        self.memory_status_label.pack(fill=tk.X, pady=(5, 0))
        
        # ========== 命令输入 ==========
        self.cmd_panel = CollapsibleFrame(main_frame, title="💬 命令输入", bg='#16213e')
        self.cmd_panel.pack(fill=tk.X, pady=(0, 8))
        
        input_row = tk.Frame(self.cmd_panel.content, bg='#16213e')
        input_row.pack(fill=tk.X)
        
        self.cmd_entry = tk.Entry(input_row, font=('Microsoft YaHei UI', 11),
                                 bg='#0f0f23', fg='#fff', insertbackground='white',
                                 relief=tk.FLAT, highlightthickness=2,
                                 highlightcolor='#00d4ff', highlightbackground='#333')
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        
        self.exec_btn = tk.Button(input_row, text="▶ 执行", font=('Microsoft YaHei UI', 10, 'bold'),
                                 bg='#00ff88', fg='#000', relief=tk.FLAT, padx=20, pady=6,
                                 command=self._on_execute, state=tk.DISABLED)
        self.exec_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        quick_frame = tk.Frame(self.cmd_panel.content, bg='#16213e')
        quick_frame.pack(fill=tk.X, pady=(8, 0))
        
        for text, cmd in [("📊 磁盘", "查看磁盘"), ("🧠 内存", "查看内存"), ("⚡ CPU", "查看CPU"),
                          ("📋 进程", "查看进程"), ("🌐 网络", "网络连接"), ("📜 日志", "系统日志")]:
            tk.Button(quick_frame, text=text, font=('Microsoft YaHei UI', 8),
                     bg='#2d3a4f', fg='#ddd', relief=tk.FLAT, padx=8, pady=2,
                     command=lambda c=cmd: self._quick_command(c)).pack(side=tk.LEFT, padx=(0, 5))
        
        # ========== 输出区域 ==========
        output_frame = tk.LabelFrame(main_frame, text=" 📺 输出结果 ",
                                    font=('Microsoft YaHei UI', 10, 'bold'),
                                    bg='#16213e', fg='#00d4ff', padx=10, pady=8)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, font=('Consolas', 10),
                                                    bg='#0f0f23', fg='#00ff88',
                                                    insertbackground='white', relief=tk.FLAT,
                                                    wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        for tag, color in [('info', '#00d4ff'), ('success', '#00ff88'), ('error', '#ff4444'),
                          ('warning', '#ffaa00'), ('command', '#ff79c6'), ('help', '#bd93f9'),
                          ('ai', '#f1c40f'), ('friendly', '#e056fd')]:
            self.output_text.tag_config(tag, foreground=color)
        
        toolbar = tk.Frame(output_frame, bg='#16213e')
        toolbar.pack(fill=tk.X, pady=(8, 0))
        
        tk.Button(toolbar, text="🗑️ 清空", font=('Microsoft YaHei UI', 8),
                 bg='#2d3a4f', fg='#ddd', relief=tk.FLAT, padx=10, pady=2,
                 command=self._clear_output).pack(side=tk.RIGHT)
        
        tk.Label(toolbar, text="💡 点击面板标题可折叠/展开", font=('Microsoft YaHei UI', 8),
                bg='#16213e', fg='#666').pack(side=tk.LEFT)
        
        self._show_welcome()
    
    def _show_welcome(self):
        self._append_output("╔════════════════════════════════════════════════════════════════════════╗\n", 'info')
        self._append_output("║          🖥️ 自动运维助手 v2.0 - 新功能                                 ║\n", 'info')
        self._append_output("╠════════════════════════════════════════════════════════════════════════╣\n", 'info')
        self._append_output("║  🤖 多 AI 支持：DeepSeek / OpenAI / 通义千问 / Ollama                  ║\n", 'info')
        self._append_output("║  📊 自动检测：连接时自动获取服务器 OS、CPU、内存信息                    ║\n", 'info')
        self._append_output("║  💾 操作记忆：按服务器 IP 保存历史，AI 像老朋友一样了解你               ║\n", 'info')
        self._append_output("╚════════════════════════════════════════════════════════════════════════╝\n\n", 'info')
    
    def _collapse_all(self):
        for p in [self.ai_panel, self.conn_panel, self.info_panel, self.cmd_panel]:
            p.collapse()
    
    def _expand_all(self):
        for p in [self.ai_panel, self.conn_panel, self.info_panel, self.cmd_panel]:
            p.expand()
    
    def _bind_events(self):
        self.cmd_entry.bind('<Return>', lambda e: self._on_execute())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _set_api_key(self):
        provider = self.current_provider.get()
        if provider == "Ollama":
            if self.ai_manager.configure_provider(provider, "ollama"):
                self.ai_panel.set_status(f"● {provider} 已配置", '#00ff88')
                self._append_output(f"[AI] {provider} 配置成功（本地模型）\n\n", 'ai')
            return
        
        api_key = simpledialog.askstring(f"设置 {provider} API Key",
                                        f"请输入 {provider} API Key:", show='*')
        if api_key:
            if self.ai_manager.configure_provider(provider, api_key):
                self.ai_panel.set_status(f"● {provider} 已配置", '#00ff88')
                self._append_output(f"[AI] {provider} API Key 配置成功\n\n", 'ai')
    
    def _set_model(self):
        provider = self.current_provider.get()
        current = self.ai_manager.providers.get(provider)
        if not current:
            return
        
        model = simpledialog.askstring("设置模型",
                                      f"当前模型: {current.default_model}\n请输入新模型名称:")
        if model:
            current.default_model = model
            self._append_output(f"[AI] 模型已设置为: {model}\n\n", 'ai')
    
    def _on_ai_toggle(self):
        provider = self.current_provider.get()
        if self.ai_mode_enabled.get():
            if not self.ai_manager.providers.get(provider, None) or \
               not self.ai_manager.providers[provider].is_configured():
                messagebox.showwarning("提示", f"请先设置 {provider} API Key")
                self.ai_mode_enabled.set(False)
                return
            self.ai_manager.set_current_provider(provider)
            self._append_output(f"[AI] 已启用 {provider}\n\n", 'ai')
            self.ai_panel.set_status(f"● {provider} 已启用", '#00ff88')
    
    def _on_connect(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        
        if not ip:
            messagebox.showerror("错误", "请输入服务器 IP")
            return
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字")
            return
        
        self.connect_btn.config(state=tk.DISABLED, text="连接中...")
        self._append_output(f"[INFO] 正在连接 {username}@{ip}...\n", 'info')
        
        def connect_thread():
            success, msg = self.ssh_manager.connect(ip, port, username, password)
            self.root.after(0, lambda: self._on_connect_result(success, msg, ip))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_connect_result(self, success: bool, msg: str, ip: str):
        if success:
            self._append_output(f"[SUCCESS] {msg}\n", 'success')
            
            # 显示服务器信息
            server_info = self.ssh_manager.get_server_info_summary()
            detected_os = self.ssh_manager.get_detected_os()
            self._append_output(f"\n[系统检测] 识别为 {detected_os}\n{server_info}\n\n", 'info')
            
            self.server_info_label.config(text=server_info)
            self.info_panel.set_status(f"● {detected_os}", '#00ff88')
            self.info_panel.expand()
            
            # 加载记忆
            self.memory_manager.load_memory(ip)
            mem_summary = self.memory_manager.get_friendly_summary()
            self.memory_status_label.config(text=f"💾 {mem_summary}")
            self._append_output(f"[记忆] {mem_summary}\n\n", 'friendly')
            
            self.conn_panel.set_status(f"● {self.ssh_manager.get_connection_info()}", '#00ff88')
            self.connect_btn.config(state=tk.DISABLED, text="✓ 已连接")
            self.disconnect_btn.config(state=tk.NORMAL)
            self.exec_btn.config(state=tk.NORMAL)
            
            for e in [self.ip_entry, self.port_entry, self.user_entry, self.pass_entry]:
                e.config(state=tk.DISABLED)
            
            self.conn_panel.collapse()
        else:
            self._append_output(f"[ERROR] {msg}\n\n", 'error')
            self.connect_btn.config(state=tk.NORMAL, text="🔌 连接")
    
    def _on_disconnect(self):
        msg = self.ssh_manager.disconnect()
        self._append_output(f"[INFO] {msg}\n\n", 'info')
        
        self.conn_panel.set_status("● 未连接", '#ff4444')
        self.info_panel.set_status("", '#888')
        self.info_panel.collapse()
        self.server_info_label.config(text="连接服务器后显示")
        self.memory_status_label.config(text="")
        
        self.connect_btn.config(state=tk.NORMAL, text="🔌 连接")
        self.disconnect_btn.config(state=tk.DISABLED)
        self.exec_btn.config(state=tk.DISABLED)
        
        for e in [self.ip_entry, self.port_entry, self.user_entry, self.pass_entry]:
            e.config(state=tk.NORMAL)
        
        self.conn_panel.expand()
    
    def _on_execute(self):
        user_input = self.cmd_entry.get().strip()
        if not user_input:
            return
        
        self.cmd_entry.delete(0, tk.END)
        self.last_user_input = user_input
        self._append_output(f">>> {user_input}\n", 'command')
        
        if self.ai_mode_enabled.get() and self.ai_manager.is_configured():
            self._process_with_ai(user_input)
        else:
            self._process_with_local(user_input)
    
    def _process_with_ai(self, user_input: str):
        self._append_output("[AI] 分析中...\n", 'ai')
        self.exec_btn.config(state=tk.DISABLED)
        
        os_type = self.ssh_manager.get_detected_os()
        server_info = self.ssh_manager.get_server_info_summary()
        memory_context = self.memory_manager.get_context_for_ai()
        
        def ai_thread():
            cmd, desc, danger, expl, note = self.ai_manager.parse_command(
                user_input, os_type, server_info, memory_context
            )
            self.root.after(0, lambda: self._on_ai_result(cmd, desc, danger, expl, note))
        
        threading.Thread(target=ai_thread, daemon=True).start()
    
    def _on_ai_result(self, cmd: str, desc: str, danger: bool, expl: str, note: str):
        self.exec_btn.config(state=tk.NORMAL)
        
        if not cmd:
            self._append_output(f"[AI] {desc}: {expl}\n\n", 'warning')
            return
        
        self._append_output(f"[AI] {desc}\n", 'ai')
        self._append_output(f"[命令] {cmd}\n", 'info')
        if note:
            self._append_output(f"[💬] {note}\n", 'friendly')
        
        if danger:
            if not messagebox.askyesno("⚠️ 危险操作", f"命令: {cmd}\n\n{expl}\n\n确定执行？"):
                self._append_output("[取消]\n\n", 'warning')
                return
        
        self._execute_command(cmd)
    
    def _process_with_local(self, user_input: str):
        cmd, desc, danger = self.nlp_processor.process(user_input)
        
        if not cmd:
            self._append_output(f"{desc}\n\n", 'help' if "帮助" in desc else 'warning')
            return
        
        self._append_output(f"[解析] {desc}\n[命令] {cmd}\n", 'info')
        
        if danger and not messagebox.askyesno("危险操作", f"命令: {cmd}\n确定执行？"):
            self._append_output("[取消]\n\n", 'warning')
            return
        
        self._execute_command(cmd)
    
    def _execute_command(self, cmd: str):
        self._append_output("[执行中...]\n", 'info')
        self.exec_btn.config(state=tk.DISABLED)
        
        def exec_thread():
            success, output = self.ssh_manager.execute_command(cmd)
            self.root.after(0, lambda: self._on_exec_result(success, output, cmd))
        
        threading.Thread(target=exec_thread, daemon=True).start()
    
    def _on_exec_result(self, success: bool, output: str, cmd: str):
        self._append_output(f"{output}\n\n", 'success' if success else 'error')
        self.exec_btn.config(state=tk.NORMAL)
        
        # 保存到记忆
        self.memory_manager.add_operation(self.last_user_input, cmd, output, success)
    
    def _quick_command(self, cmd: str):
        if not self.ssh_manager.is_connected():
            messagebox.showwarning("提示", "请先连接服务器")
            return
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self._on_execute()
    
    def _append_output(self, text: str, tag: str = None):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def _clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def _on_close(self):
        if self.ssh_manager.is_connected():
            if messagebox.askyesno("确认退出", "SSH 连接仍在，确定退出？"):
                self.ssh_manager.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

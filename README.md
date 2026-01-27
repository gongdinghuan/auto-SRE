# 🖥️ 自动运维助手 (Auto-Ops Assistant)

一个基于 Python 的智能运维工具，支持 **DeepSeek AI** 自然语言解析，通过 SSH 远程管理 Linux 服务器。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🤖 **AI 智能解析** | 集成 DeepSeek 大模型，理解任意自然语言需求 |
| 🔗 **SSH 远程连接** | 安全连接 Linux 服务器执行命令 |
| 💬 **自然语言操作** | 用中文描述需求，自动生成 Linux 命令 |
| ⚡ **快捷命令** | 一键执行常用运维操作 |
| ⚠️ **安全防护** | 危险命令自动识别，二次确认保护 |

## 📦 安装

```bash
# 克隆或进入项目目录
cd c:\Users\Administrator\SRE

# 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

```bash
python main.py
```

## 📖 使用说明

### 1. 配置 AI（可选但推荐）
- 点击 **「设置 API Key」** 输入 DeepSeek API Key
- 勾选 **「启用 AI 解析」** 开关
- API Key 获取：https://platform.deepseek.com

### 2. 连接服务器
- 输入服务器 IP、端口、用户名、密码
- 点击 **「连接服务器」**

### 3. 执行命令
使用自然语言描述您的需求：

```
查看磁盘空间          → df -h
查看内存使用情况      → free -h
找出 CPU 占用最高的进程 → ps aux --sort=-%cpu | head -10
检查 nginx 是否运行   → systemctl status nginx
```

## 🗂️ 项目结构

```
├── main.py            # 程序入口
├── gui.py             # Tkinter 图形界面
├── ssh_manager.py     # SSH 连接管理
├── nlp_processor.py   # 本地命令匹配
├── deepseek_ai.py     # DeepSeek AI 集成
└── requirements.txt   # 项目依赖
```

## 📋 支持的自然语言命令

| 类别 | 示例 |
|------|------|
| 系统信息 | 磁盘空间、内存、CPU、系统信息、负载 |
| 进程服务 | 查看进程、服务状态 |
| 网络 | 网络连接、端口、IP地址 |
| 日志 | 系统日志、登录记录 |
| Docker | 容器列表、镜像列表 |
| 系统操作 | 重启服务器、更新系统 |

## ⚙️ 依赖

- Python 3.8+
- paramiko - SSH 连接
- openai - DeepSeek API 调用
- tkinter - 图形界面（Python 内置）

## 📄 License

MIT License

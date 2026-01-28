# 🖥️ 自动运维助手 v2.0

智能运维工具，集成多家 AI 大模型，通过自然语言远程管理 Linux 服务器。

## ✨ 新功能

| 功能 | 描述 |
|------|------|
| 🤖 **多 AI 支持** | DeepSeek / OpenAI / 通义千问 / Ollama |
| 📊 **自动检测** | 连接时自动识别服务器 OS、CPU、内存 |
| 💾 **操作记忆** | 按 IP 保存历史，AI 像老朋友一样了解你 |

## 📦 安装

```bash
pip install -r requirements.txt
```

## 🚀 运行

```bash
python main.py
```

## 📖 使用流程

1. **选择 AI** → 下拉选择提供商 → 设置 API Key → 启用 AI
2. **连接服务器** → 输入 IP/用户名/密码 → 自动检测系统信息
3. **执行命令** → 用自然语言描述需求 → AI 智能生成命令

## 🗂️ 项目结构

```
├── main.py            # 入口
├── gui.py             # 界面
├── ssh_manager.py     # SSH + 自动检测
├── ai_providers.py    # 多 AI 提供商
├── memory_manager.py  # 操作记忆
├── nlp_processor.py   # 本地命令匹配
└── requirements.txt   # 依赖
```

## 🤖 AI 提供商

| 提供商 | API 地址 | 模型 |
|--------|----------|------|
| DeepSeek | api.deepseek.com | deepseek-chat |
| OpenAI | api.openai.com | gpt-4o-mini |
| 通义千问 | dashscope.aliyuncs.com | qwen-turbo |
| Ollama | localhost:11434 | qwen2.5:7b |

## 📄 License

MIT

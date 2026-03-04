# 🤖 NapCat Video Bot - 开源QQ视频下载机器人

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docker-compose.yml)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](requirements.txt)

一个基于 NapCat 的 QQ 机器人，支持视频下载、直播录制、文件处理等功能。

## ✨ 功能特性

- 🎥 **视频下载** - 支持 YouTube、Bilibili 等平台
- 📹 **直播录制** - 实时录制直播流
- 🗂️ **文件管理** - 集成 Alist 网盘，支持多种存储后端
- 🔄 **任务队列** - 异步处理，支持并发下载
- 🌐 **Web界面** - 实时查看任务状态和进度
- 📱 **QQ交互** - 私聊/群聊命令支持
- ☁️ **多云存储** - 支持 Alist、S3、R2、阿里云OSS等

## 🏗️ 架构设计

```
┌─────────────┐    WebSocket    ┌──────────────┐    HTTP API    ┌─────────────┐
│   NapCat    │ ←────────────→ │  Video Bot   │ ─────────────→ │   Alist     │
│  (QQ协议)   │                 │ (Python应用) │                │  (网盘)     │
└─────────────┘                 └──────────────┘                └─────────────┘
        ↓                               ↓                               ↓
   QQ消息接收                      处理下载任务                      文件存储管理
```

## 🚀 快速开始

### 1. 环境要求

- Docker & Docker Compose
- Python 3.8+ (如果不使用 Docker)
- QQ 账号

### 2. 克隆项目

```bash
git clone https://github.com/yourusername/napcat-ytdlp.git
cd napcat-ytdlp
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 4. 启动服务

```bash
# Docker Compose 部署
docker-compose up -d

# 或者手动部署
pip install -r requirements.txt
python app/main.py
```

### 5. 配置 NapCat

访问 `http://localhost:6099/webui` 扫码登录 QQ

## 📁 项目结构

```
napcat-ytdlp/
├── app/                    # Video Bot 核心代码
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置文件
│   ├── handlers/          # 消息处理器
│   ├── executor/          # 下载执行器
│   └── db.py              # 数据库操作
├── docker-compose.yml     # Docker 编排文件
├── .env.example          # 环境变量模板
├── requirements.txt       # Python 依赖
├── ecosystem.config.js   # PM2 配置
└── README.md             # 项目文档
```

## ⚙️ 配置说明

### 基础配置 (.env)

```env
# QQ 机器人配置
MASTER_QQ=314389463                    # 管理员QQ号
NAPCAT_ACCOUNTQQ=你的QQ号              # 机器人QQ号
NAPCAT_TOKEN=your_token               # NapCat API Token

# 服务端口
FLASK_PORT=5000                        # Video Bot Web端口
NAPCAT_HTTP_PORT=3000                  # NapCat HTTP端口
NAPCAT_WS_PORT=3001                    # NapCat WebSocket端口

# 下载配置
DOWNLOAD_DIR=/tmp/alist_downloads      # 下载目录
MAX_CONCURRENT_TASKS=2                # 最大并发任务数

# LLM配置 (可选)
LLM_API_KEY=your_api_key              # MiniMax API Key
LLM_API_URL=https://api.minimaxi.com/v1/chat/completions
LLM_MODEL=MiniMax-M2.5
```

### 存储配置

#### Alist 本地存储
```yaml
alist:
  image: xhofe/alist:latest
  volumes:
    - ./data/alist:/opt/alist/data
    - /path/to/downloads:/mnt/downloads  # 本地存储路径
```

#### S3 兼容存储
```yaml
alist:
  image: xhofe/alist:latest
  environment:
    - S3_ENDPOINT=https://s3.amazonaws.com
    - S3_ACCESS_KEY_ID=your_access_key
    - S3_SECRET_ACCESS_KEY=your_secret_key
    - S3_BUCKET=your_bucket
```

#### Cloudflare R2
```yaml
alist:
  image: xhofe/alist:latest
  environment:
    - R2_ACCOUNT_ID=your_account_id
    - R2_ACCESS_KEY_ID=your_access_key
    - R2_SECRET_ACCESS_KEY=your_secret_key
    - R2_BUCKET=your_bucket
```

## 📖 使用指南

### QQ 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/下载 链接` | 下载视频 | `/下载 https://youtube.com/watch?v=xxx` |
| `/录播 链接` | 录制直播 | `/录播 https://live.bilibili.com/xxx` |
| `/任务` | 查看任务列表 | `/任务` |
| `/帮助` | 显示帮助 | `/帮助` |

### API 接口

```bash
# 获取任务列表
curl http://localhost:5000/api/tasks

# 创建下载任务
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"action":"download","url":"https://youtube.com/watch?v=xxx"}'

# 获取任务状态
curl http://localhost:5000/api/tasks/{task_id}
```

## 🔧 高级配置

### 自定义存储后端

支持多种存储后端，通过 Alist 配置：

- **本地存储**：直接挂载磁盘
- **阿里云OSS**：配置OSS参数
- **腾讯云COS**：配置COS参数
- **七牛云Kodo**：配置Kodo参数
- **又拍云US3**：配置US3参数

### 反向代理配置

#### Nginx 示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /alist {
        proxy_pass http://localhost:5244;
    }
}
```

## 🛠️ 开发指南

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app/main.py

# 运行测试
python -m pytest tests/
```

### 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2024-03-05)
- ✨ 初始版本发布
- 🎥 支持视频下载和直播录制
- 🗂️ 集成 Alist 网盘
- 📱 QQ 私聊/群聊支持
- 🌐 Web 管理界面

## 🤝 贡献者

感谢所有为这个项目做出贡献的开发者！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [NapCat](https://github.com/NapNeko/NapCatQQ) - QQ 机器人框架 (MIT License)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载工具 (Unlicense)
- [Alist](https://github.com/alist-org/alist) - 网盘系统 (AGPL-3.0 License)
- [Flask](https://github.com/pallets/flask) - Web 框架 (BSD-3-Clause License)

### 📄 开源协议声明

本项目基于以下开源项目构建：

- **NapCat**: 本项目使用 NapCat 作为 QQ 协议层，NapCat 遵循 MIT 许可证
- **yt-dlp**: 使用 yt-dlp 进行视频下载，遵循 Unlicense 许可证  
- **Alist**: 集成 Alist 作为文件管理系统，遵循 AGPL-3.0 许可证

本项目核心代码遵循 MIT 许可证，但请注意：
- 如果修改或分发 Alist 相关代码，需要遵循 AGPL-3.0 许可证
- 使用本项目时请同时遵守各依赖项目的许可证条款

## 📞 支持

如果你遇到问题或有建议，请：

- 🐛 [提交 Issue](https://github.com/yourusername/napcat-ytdlp/issues)
- 💬 [讨论区](https://github.com/yourusername/napcat-ytdlp/discussions)
- 📧 邮件：your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

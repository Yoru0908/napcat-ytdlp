# 🚀 部署指南

本文档详细介绍了如何在不同环境中部署 NapCat Video Bot。

## 📋 部署方式

### 1. Docker Compose 部署 (推荐)

#### 优点
- 一键部署，环境隔离
- 自动管理依赖关系
- 易于扩展和维护

#### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/napcat-ytdlp.git
cd napcat-ytdlp

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 3. 启动服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f video-bot
```

#### 配置要点

```env
# 必填配置
MASTER_QQ=314389463                    # 管理员QQ号
NAPCAT_ACCOUNTQQ=1873755396            # 机器人QQ号
NAPCAT_TOKEN=your_napcat_token         # NapCat Token
ALIST_PASSWORD=your_alist_password     # Alist密码

# 可选配置
DOWNLOAD_DIR=/mnt/downloads           # 下载目录
MAX_CONCURRENT_TASKS=2                 # 并发任务数
LLM_API_KEY=your_minimax_key          # AI功能
```

### 2. 手动部署

#### 系统要求
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python 3.8+
- FFmpeg
- Node.js (可选，用于NapCat)

#### 步骤

```bash
# 1. 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg curl

# 2. 安装 yt-dlp
sudo pip3 install yt-dlp

# 3. 克隆项目
git clone https://github.com/yourusername/napcat-ytdlp.git
cd napcat-ytdlp

# 4. 安装Python依赖
pip3 install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
nano .env

# 6. 启动Video Bot
python3 app/main.py
```

### 3. PM2 进程管理部署

#### 安装 PM2

```bash
npm install -g pm2
```

#### 启动应用

```bash
# 使用PM2启动
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs video-bot

# 设置开机自启
pm2 startup
pm2 save
```

## 🗂️ 存储配置

### 本地存储

```yaml
# docker-compose.yml
alist:
  volumes:
    - /path/to/your/downloads:/downloads
```

### S3 兼容存储

#### AWS S3

```env
STORAGE_TYPE=s3
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY_ID=AKIA...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET=my-video-bot
S3_REGION=us-east-1
```

#### 阿里云OSS

```env
STORAGE_TYPE=oss
OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
OSS_ACCESS_KEY_ID=LTAI...
OSS_SECRET_ACCESS_KEY=...
OSS_BUCKET=my-video-bot
```

#### 腾讯云COS

```env
STORAGE_TYPE=cos
COS_SECRET_ID=AKID...
COS_SECRET_KEY=...
COS_REGION=ap-beijing
COS_BUCKET=my-video-bot
```

#### Cloudflare R2

```env
STORAGE_TYPE=r2
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=my-video-bot
```

## 🌐 反向代理配置

### Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Video Bot
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Alist
    location /alist {
        proxy_pass http://localhost:5244;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # NapCat WebUI
    location /napcat {
        proxy_pass http://localhost:6099;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caddy

```caddyfile
your-domain.com {
    reverse_proxy localhost:5000
    
    handle /alist {
        reverse_proxy localhost:5244
    }
    
    handle /napcat {
        reverse_proxy localhost:6099
    }
}
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### 2. SSL 证书

#### Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 访问控制

```nginx
# 限制IP访问
location /admin {
    allow 192.168.1.0/24;
    deny all;
    proxy_pass http://localhost:5000;
}

# 基础认证
location /private {
    auth_basic "Restricted Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5000;
}
```

## 📊 监控配置

### 1. 健康检查

```bash
#!/bin/bash
# health-check.sh

# 检查Video Bot
if curl -f http://localhost:5000/api/tasks > /dev/null 2>&1; then
    echo "✅ Video Bot: OK"
else
    echo "❌ Video Bot: FAILED"
    # 发送告警
fi

# 检查Alist
if curl -f http://localhost:5244/api/public/settings > /dev/null 2>&1; then
    echo "✅ Alist: OK"
else
    echo "❌ Alist: FAILED"
fi

# 检查NapCat
if curl -f http://localhost:3002/get_status_info > /dev/null 2>&1; then
    echo "✅ NapCat: OK"
else
    echo "❌ NapCat: FAILED"
fi
```

### 2. 日志管理

```bash
# logrotate 配置
cat > /etc/logrotate.d/video-bot << EOF
/path/to/video-bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 user user
}
EOF
```

## 🔧 故障排除

### 常见问题

#### 1. NapCat 连接失败

```bash
# 检查端口
netstat -tlnp | grep :3000
netstat -tlnp | grep :3001

# 检查日志
docker logs napcat
```

#### 2. 下载失败

```bash
# 检查磁盘空间
df -h

# 检查 yt-dlp
yt-dlp --version

# 测试下载
yt-dlp "https://www.youtube.com/watch?v=test"
```

#### 3. Alist 访问问题

```bash
# 检查权限
ls -la /path/to/downloads

# 重启Alist
docker restart alist
```

### 性能优化

#### 1. 并发限制

```env
# .env
MAX_CONCURRENT_TASKS=2  # 根据服务器性能调整
```

#### 2. 缓存配置

```yaml
# docker-compose.yml
services:
  video-bot:
    environment:
      - REDIS_URL=redis://redis:6379/0
  redis:
    image: redis:alpine
    volumes:
      - ./data/redis:/data
```

## 📱 移动端访问

### PWA 配置

```json
{
  "name": "Video Bot",
  "short_name": "VBot",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1890ff"
}
```

## 🔄 备份策略

### 数据备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/video-bot"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp /app/data/bot.db $BACKUP_DIR/bot_$DATE.db

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

# 备份下载文件 (可选)
# tar -czf $BACKUP_DIR/downloads_$DATE.tar.gz /path/to/downloads

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 自动备份

```bash
# 添加到 crontab
0 2 * * * /path/to/backup.sh
```

---

## 📞 获取帮助

如果在部署过程中遇到问题：

1. 查看 [Issues](https://github.com/yourusername/napcat-ytdlp/issues)
2. 加入 [讨论区](https://github.com/yourusername/napcat-ytdlp/discussions)
3. 提交新的 Issue

记得在 Issue 中包含：
- 操作系统版本
- 部署方式
- 错误日志
- 配置文件 (隐去敏感信息)

# ===========================================
# NapCat Video Bot 配置文件
# ===========================================
# 
# 本项目基于以下开源项目构建：
# - NapCat: https://github.com/NapNeko/NapCatQQ (MIT License)
# - yt-dlp: https://github.com/yt-dlp/yt-dlp (Unlicense)
# - Alist: https://github.com/alist-org/alist (AGPL-3.0 License)
# 
# 请遵守各依赖项目的许可证条款
# ===========================================

# 默认配置 (可通过环境变量覆盖)
import os

# QQ 机器人配置
MASTER_QQ = os.getenv('MASTER_QQ', '123456789')
NAPCAT_ACCOUNTQQ = os.getenv('NAPCAT_ACCOUNTQQ', '987654321')

# Flask 配置
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# 下载配置
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', '/tmp/alist_downloads')
LOG_DIR = os.getenv('LOG_DIR', 'data/logs')
DB_PATH = os.getenv('DB_PATH', 'data/bot.db')
MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '2'))

# Alist 配置
ALIST_URL = os.getenv('ALIST_URL', 'http://localhost:5244')
ALIST_USERNAME = os.getenv('ALIST_USERNAME', 'admin')
ALIST_PASSWORD = os.getenv('ALIST_PASSWORD', '')
ALIST_PUBLIC_URL = os.getenv('ALIST_PUBLIC_URL', '')

# NapCat 配置
NAPCAT_WS_URL = os.getenv('NAPCAT_WS_URL', 'ws://127.0.0.1:3001')
NAPCAT_HTTP_URL = os.getenv('NAPCAT_HTTP_URL', 'http://127.0.0.1:3000')
NAPCAT_HTTP_TOKEN = os.getenv('NAPCAT_TOKEN', '')
NAPCAT_WS_TOKEN = os.getenv('NAPCAT_WS_TOKEN', '')

# LLM 配置 (可选)
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.minimaxi.com/v1/chat/completions')
LLM_MODEL = os.getenv('LLM_MODEL', 'MiniMax-M2.5')

# 公网访问配置
VIDEOBOT_PUBLIC_URL = os.getenv('VIDEOBOT_PUBLIC_URL', '')

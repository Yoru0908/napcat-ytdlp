#!/bin/bash
# 启动视频机器人

cd ~/video-bot/app

# 设置 PATH
export PATH="/vol1/@appcenter/nodejs_v22/bin:$PATH"

# 启动 Flask
nohup python3 main.py > /tmp/flask.log 2>&1 &

echo "Flask 已启动"
echo "访问 http://192.168.3.11:5000 查看控制台"

#!/usr/bin/env python3
"""
视频机器人主入口
"""

import os
import json
import asyncio
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from threading import Thread

import config
import db
import task_queue
from handlers.napcat import start_napcat_listener

app = Flask(__name__)

# 初始化数据库
db.init_db()

# SSE 客户端存储
sse_clients = []


# ============== 页面路由 ==============

@app.route('/')
def index():
    """前端页面"""
    return render_template('index.html')


# ============== API 路由 ==============

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    tasks = db.get_all_tasks()
    # 添加队列状态
    tasks.append({
        'queue_size': task_queue.get_pending_count()
    })
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    data = request.json
    action = data.get('action', 'download')
    url = data.get('url')
    input_file = data.get('input_file')
    output_file = data.get('output_file')

    if action in ['download', 'record']:
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        task_id = task_queue.submit_download(url, action)
    elif action in ['transcode', 'cut', 'merge', 'extract_audio']:
        if not input_file or not output_file:
            return jsonify({'error': 'input_file and output_file are required'}), 400
        task_id = task_queue.submit_ffmpeg(action, input_file, output_file, **data)
    else:
        return jsonify({'error': 'Invalid action'}), 400

    return jsonify({'task_id': task_id})


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除/停止任务"""
    success = task_queue.stop_task(task_id)
    if success:
        db.delete_task(task_id)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Task not found'}), 404


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取单个任务详情"""
    task = db.get_task(task_id)
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404


# ============== 日志路由 ==============

@app.route('/api/logs/<task_id>')
def get_logs(task_id):
    """获取任务日志 (SSE)"""

    @stream_with_context
    def generate():
        log_file = f"{config.LOG_DIR}/{task_id}.log"
        last_size = 0

        while True:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                if size > last_size:
                    with open(log_file, 'r') as f:
                        f.seek(last_size)
                        new_content = f.read()
                        last_size = size
                        yield f"data: {json.dumps({'content': new_content})}\n\n"

            import time
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')


# ============== SSE 实时进度 ==============

@app.route('/events')
def events():
    """SSE 实时进度推送"""

    def subscribe():
        task_queue.register_callback(push_progress)
        try:
            while True:
                import time
                time.sleep(1)
        except GeneratorExit:
            pass

    def push_progress(task_id, status, progress):
        pass  # 注册回调，实际推送在下面

    return Response(stream_with_context(subscribe()), mimetype='text/event-stream')


# 简单的 SSE 推送机制
def broadcast_progress(task_id, status, progress):
    """广播进度到所有 SSE 客户端"""
    data = json.dumps({
        'task_id': task_id,
        'status': status,
        'progress': progress
    })
    # 这里简化处理，实际可以用 redis pub/sub
    for client in sse_clients:
        try:
            client.put(data)
        except:
            pass


# ============== 启动 ==============

def start_napcat():
    """启动 Napcat 监听器 (后台线程)"""
    print("开始连接 Napcat...")
    import config
    print(f"URL: {config.NAPCAT_WS_URL}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_napcat_listener())
    except Exception as e:
        print(f"Napcat 连接错误: {e}")


if __name__ == '__main__':
    # 启动 Napcat 监听线程
    print("启动 Napcat 监听线程...")
    napcat_thread = Thread(target=start_napcat)
    napcat_thread.start()

    # 启动 Flask
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        threaded=True
    )

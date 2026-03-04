import uuid
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from db import create_task, update_task_status, get_task
from executor.ytdlp import ytdlp_executor
from executor.ffmpeg import ffmpeg_executor
import config

# 线程池，最大并发数限制
executor = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_TASKS)

# 任务回调 - SSE 推送
task_callbacks = []


def register_callback(callback):
    """注册任务状态回调"""
    task_callbacks.append(callback)


def notify_progress(task_id, status, progress=None):
    """通知所有回调"""
    for cb in task_callbacks:
        try:
            cb(task_id, status, progress)
        except Exception as e:
            print(f"Callback error: {e}")


def generate_task_id():
    """生成任务ID"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:4]


def submit_download(url, action='download'):
    """提交下载任务"""
    task_id = generate_task_id()

    # 确定文件扩展名
    ext = 'mp4' if action == 'download' else 'mkv'
    output_file = f"{config.DOWNLOAD_DIR}/{task_id}.{ext}"
    log_file = f"{config.LOG_DIR}/{task_id}.log"

    # 创建任务记录
    create_task(task_id, action, url, output_file)

    # 提交到线程池
    future = executor.submit(run_task, task_id, action, url, output_file, log_file)

    return task_id


def submit_ffmpeg(action, input_file, output_file, **kwargs):
    """提交 FFmpeg 任务"""
    task_id = generate_task_id()
    log_file = f"{config.LOG_DIR}/{task_id}.log"

    # 解析操作参数
    if action == 'transcode':
        options = kwargs.get('options')
        create_task(task_id, action, input_file, output_file)
        future = executor.submit(ffmpeg_executor.start_transcode,
                                  task_id, input_file, output_file, log_file, options)
    elif action == 'cut':
        start_time = kwargs.get('start_time')
        duration = kwargs.get('duration')
        create_task(task_id, action, input_file, output_file)
        future = executor.submit(ffmpeg_executor.start_cut,
                                  task_id, input_file, output_file, start_time, duration, log_file)
    elif action == 'merge':
        input_files = kwargs.get('input_files')
        create_task(task_id, action, f"merge:{len(input_files)} files", output_file)
        future = executor.submit(ffmpeg_executor.start_merge,
                                  task_id, input_files, output_file, log_file)
    elif action == 'extract_audio':
        create_task(task_id, action, input_file, output_file)
        future = executor.submit(ffmpeg_executor.extract_audio,
                                  task_id, input_file, output_file, log_file)

    return task_id


def run_task(task_id, action, url, output_file, log_file):
    """执行 yt-dlp 任务"""
    try:
        if action == 'download':
            ytdlp_executor.start_download(task_id, url, output_file, log_file)
        elif action == 'record':
            ytdlp_executor.start_record(task_id, url, output_file, log_file)

        # 监控进度
        while ytdlp_executor.is_running(task_id):
            progress = ytdlp_executor.check_progress(task_id, log_file)
            if progress is not None:
                update_task_status(task_id, 'running', progress=progress)
                notify_progress(task_id, 'running', progress)
            import time
            time.sleep(2)

        # 检查是否正常完成
        if os.path.exists(output_file):
            # 文件下载完成，通知用户
            filename = os.path.basename(output_file)
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            file_size_mb = file_size / 1024 / 1024

            # 存到数据库，标记完成
            alist_url = f"文件已下载: {filename} ({file_size_mb:.1f}MB)"
            update_task_status(task_id, 'completed', progress=100, alist_url=alist_url)

            # 通知用户下载完成
            try:
                from handlers.napcat import napcat_handler
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                msg = f"🟢 下载任务完成！\n📁 文件: {filename}\n📦 大小: {file_size_mb:.1f}MB\n🚀 正在尝试上传至QQ..."
                # 先发一条文字通知
                loop.run_until_complete(napcat_handler.send_simple_msg(config.MASTER_QQ, msg))
                # 尝试发送文件
                loop.run_until_complete(napcat_handler.send_file(config.MASTER_QQ, output_file))
                loop.close()
                print(f"已通知用户")
            except Exception as e:
                print(f"通知失败: {e}")
            notify_progress(task_id, 'completed', 100)
        else:
            update_task_status(task_id, 'failed')
            notify_progress(task_id, 'failed', 0)

    except Exception as e:
        print(f"Task error: {e}")
        update_task_status(task_id, 'failed')
        notify_progress(task_id, 'failed', 0)


def stop_task(task_id):
    """停止任务"""
    task = get_task(task_id)
    if not task:
        return False

    action = task['action']

    if action in ['download', 'record']:
        ytdlp_executor.stop(task_id)
    else:
        ffmpeg_executor.stop(task_id)

    return True


def get_pending_count():
    """获取等待中的任务数"""
    return executor._work_queue.qsize()

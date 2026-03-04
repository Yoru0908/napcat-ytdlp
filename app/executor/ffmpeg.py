import subprocess
import os
import signal
from db import update_task_status

class FFmpegExecutor:
    """FFmpeg 执行器"""

    def __init__(self):
        self.processes = {}

    def start_transcode(self, task_id, input_file, output_file, log_file, options=None):
        """启动转码任务"""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        cmd = ['ffmpeg', '-i', input_file]
        if options:
            cmd.extend(options)
        cmd.extend(['-y', output_file])  # -y 覆盖输出

        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)

        return proc.pid

    def start_cut(self, task_id, input_file, output_file, start_time, duration, log_file):
        """剪切视频片段"""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        cmd = [
            'ffmpeg', '-i', input_file,
            '-ss', start_time,
            '-t', str(duration),
            '-c', 'copy',  # 直接复制，不重新编码
            '-y', output_file
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)

        return proc.pid

    def start_merge(self, task_id, input_files, output_file, log_file):
        """合并视频"""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # 创建临时文件列表
        list_file = f"data/logs/{task_id}_list.txt"
        with open(list_file, 'w') as f:
            for file in input_files:
                f.write(f"file '{file}'\n")

        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-y', output_file
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)

        return proc.pid

    def extract_audio(self, task_id, input_file, output_file, log_file):
        """提取音频"""
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        cmd = [
            'ffmpeg', '-i', input_file,
            '-vn', '-acodec', 'libmp3lame',
            '-y', output_file
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)

        return proc.pid

    def stop(self, task_id):
        """停止任务"""
        proc = self.processes.get(task_id)
        if proc:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=10)
            except Exception as e:
                print(f"Error stopping task {task_id}: {e}")
            finally:
                del self.processes[task_id]
                update_task_status(task_id, 'stopped')

    def is_running(self, task_id):
        """检查任务是否还在运行"""
        proc = self.processes.get(task_id)
        if proc:
            return proc.poll() is None
        return False


# 全局实例
ffmpeg_executor = FFmpegExecutor()

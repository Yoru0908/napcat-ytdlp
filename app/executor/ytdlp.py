import subprocess
import os
import signal
import re
from db import update_task_status

class YtdlpExecutor:
    def __init__(self):
        self.processes = {}

    def start_download(self, task_id, url, output_path, log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        proc = subprocess.Popen(
            [
                'yt-dlp',
                '-f', 'bv[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/best',
                '--merge-output-format', 'mp4',
                '--remux-video', 'mp4',
                '-o', output_path,
                '--no-warnings',
                '--progress',
                url
            ],
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)
        return proc.pid

    def start_record(self, task_id, url, output_path, log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        proc = subprocess.Popen(
            [
                'yt-dlp',
                '--live-from-start',
                '--wait-for-video', '15',
                '-f', 'bv[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/best',
                '--merge-output-format', 'mp4',
                '-o', output_path,
                '--no-warnings',
                url
            ],
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        self.processes[task_id] = proc
        update_task_status(task_id, 'running', pid=proc.pid)
        return proc.pid

    def stop(self, task_id):
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
        proc = self.processes.get(task_id)
        if proc:
            return proc.poll() is None
        return False

    def check_progress(self, task_id, log_file):
        if not os.path.exists(log_file):
            return 0
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            lines = content.split('\n')
            for line in reversed(lines):
                if '%' in line and 'download' in line.lower():
                    match = re.search(r'(\d+\.?\d*)%', line)
                    if match:
                        return float(match.group(1))
            if 'has already been downloaded' in content or '[download] 100%' in content:
                return 100
        except Exception as e:
            print(f"Error reading progress: {e}")
        return None


ytdlp_executor = YtdlpExecutor()

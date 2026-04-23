import sqlite3
import os
from datetime import datetime
from config import DB_PATH

def init_db():
    """初始化数据库"""
    os.makedirs(os.path.dirname(DB_PATH) or "data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            action TEXT NOT NULL,
            url TEXT,
            output_file TEXT,
            status TEXT DEFAULT 'pending',
            progress REAL DEFAULT 0,
            pid INTEGER,
            alist_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
    finally:
        conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

def create_task(task_id, action, url, output_file):
    """创建新任务"""
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO tasks (task_id, action, url, output_file, status)
                    VALUES (?, ?, ?, ?, 'pending')''',
                  (task_id, action, url, output_file))
        conn.commit()
    finally:
        conn.close()

def update_task_status(task_id, status, progress=None, pid=None, alist_url=None):
    """更新任务状态"""
    conn = get_conn()
    try:
        c = conn.cursor()
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]

        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        if pid is not None:
            updates.append("pid = ?")
            params.append(pid)
        if alist_url is not None:
            updates.append("alist_url = ?")
            params.append(alist_url)

        params.append(task_id)
        c.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?", params)
        conn.commit()
    finally:
        conn.close()

def get_task(task_id):
    """获取单个任务"""
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = c.fetchone()
    finally:
        conn.close()

    if row:
        columns = ["id", "task_id", "action", "url", "output_file", "status",
                   "progress", "pid", "alist_url", "created_at", "updated_at"]
        return dict(zip(columns, row))
    return None

def get_all_tasks():
    """获取所有任务"""
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = c.fetchall()
    finally:
        conn.close()

    columns = ["id", "task_id", "action", "url", "output_file", "status",
               "progress", "pid", "alist_url", "created_at", "updated_at"]
    return [dict(zip(columns, row)) for row in rows]

def delete_task(task_id):
    """删除任务"""
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()

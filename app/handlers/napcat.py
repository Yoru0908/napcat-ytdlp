import json
import asyncio
import websockets
import requests
import config
import task_queue


class NapcatHandler:
    """Napcat 消息处理器 - WebSocket 接收，HTTP API 发送"""

    def __init__(self):
        self.ws = None
        self.bot_qq = None

    # =====================
    # HTTP API 发送
    # =====================

    def _http_post(self, endpoint, payload, timeout=10):
        """通用 HTTP 发送到 NapCat API"""
        url = f"{config.NAPCAT_HTTP_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {config.NAPCAT_HTTP_TOKEN}"}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"HTTP API 调用失败 [{endpoint}]: {e}")
            return None

    async def send_simple_msg(self, user_id, message):
        """发送私聊文字消息（HTTP API）"""
        self._http_post("send_private_msg", {
            "user_id": int(user_id),
            "message": message
        })
        print(f"[HTTP] 发送私聊 -> {user_id}: {str(message)[:50]}")

    async def send_group_message(self, group_id, message):
        """发送群消息（HTTP API）"""
        self._http_post("send_group_msg", {
            "group_id": int(group_id),
            "message": message
        })
        print(f"[HTTP] 发送群消息 -> {group_id}: {str(message)[:50]}")

    async def send_reply(self, data, message):
        """回复私聊消息（HTTP API）"""
        user_id = data.get('user_id')
        if not user_id:
            return
        await self.send_simple_msg(user_id, message)

    async def send_group_reply(self, data, message):
        """回复群消息（HTTP API）"""
        group_id = data.get('group_id')
        if not group_id:
            return
        await self.send_group_message(group_id, message)

    def _get_alist_direct_link(self, filename):
        """获取 Alist 直链"""
        try:
            # 登录获取 token
            login_resp = requests.post(
                f"{config.ALIST_URL}/api/auth/login",
                json={"username": config.ALIST_USERNAME, "password": config.ALIST_PASSWORD},
                timeout=10
            )
            token = login_resp.json().get("data", {}).get("token", "")
            if not token:
                print("[Alist] 登录失败")
                return None

            # 获取文件直链
            fs_resp = requests.post(
                f"{config.ALIST_URL}/api/fs/get",
                headers={"Authorization": token},
                json={"path": f"/downloads/{filename}"},
                timeout=10
            )
            data = fs_resp.json()
            if data.get("code") == 200:
                raw_url = data["data"].get("raw_url", "")
                if raw_url:
                    print(f"[Alist] 获取直链成功: {raw_url[:80]}")
                    return raw_url
                # 本地存储没有 raw_url，用 Cloudflare 公网代理链接
                sign = data["data"].get("sign", "")
                public_base = getattr(config, 'ALIST_PUBLIC_URL', config.ALIST_URL)
                proxy_url = f"{public_base}/d/downloads/{filename}"
                if sign:
                    proxy_url += f"?sign={sign}"
                print(f"[Alist] 使用公网链接: {proxy_url[:80]}")
                return proxy_url
            else:
                print(f"[Alist] 获取文件信息失败: {data.get('message')}")
                return None
        except Exception as e:
            print(f"[Alist] 直链获取异常: {e}")
            return None

    async def send_file(self, user_id, file_path):
        """发送文件/媒体到 QQ - 小文件直传，大文件走 Alist 直链"""
        import os

        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False

        filename = os.path.basename(file_path)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / 1024 / 1024

        # 容器内路径（NapCat 容器挂载了 /tmp/alist_downloads）
        container_path = f"/tmp/alist_downloads/{filename}"

        SIZE_THRESHOLD_MB = 100

        if file_size_mb < SIZE_THRESHOLD_MB:
            # === 小文件：直接通过 NapCat 上传 ===
            print(f"[上传] 小文件模式 ({file_size_mb:.1f}MB < {SIZE_THRESHOLD_MB}MB)")

            # 发 CQ 码媒体消息
            if ext in ('mp3', 'wav', 'aac', 'm4a', 'ogg'):
                cq = f"[CQ:record,file=file://{container_path}]"
            elif ext in ('mp4', 'avi', 'mov', 'mkv', 'flv'):
                cq = f"[CQ:video,file=file://{container_path}]"
            elif ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                cq = f"[CQ:image,file=file://{container_path}]"
            else:
                cq = None

            if cq:
                self._http_post("send_private_msg", {
                    "user_id": int(user_id),
                    "message": cq
                }, timeout=300)
                print(f"[HTTP] 发送媒体 CQ 码: {cq[:60]}")

            # 上传物理文件
            result = self._http_post("upload_private_file", {
                "user_id": int(user_id),
                "file": container_path,
                "name": filename
            }, timeout=600)
            if result:
                print(f"[HTTP] 文件上传成功: {filename}")
                return True
            else:
                print(f"[HTTP] 文件上传失败，尝试 Alist 直链...")
                # 失败则 fallback 到 Alist
                return await self._send_alist_link(user_id, filename, file_size_mb)
        else:
            # === 大文件：走 Alist 直链 ===
            print(f"[上传] 大文件模式 ({file_size_mb:.1f}MB >= {SIZE_THRESHOLD_MB}MB)，使用 Alist 直链")
            return await self._send_alist_link(user_id, filename, file_size_mb)

    async def _send_alist_link(self, user_id, filename, file_size_mb):
        """通过 Alist 直链发送下载链接"""
        link = self._get_alist_direct_link(filename)
        if link:
            msg = (
                f"📁 文件: {filename}\n"
                f"📦 大小: {file_size_mb:.1f}MB\n"
                f"🔗 下载链接:\n{link}"
            )
            await self.send_simple_msg(user_id, msg)
            print(f"[Alist] 直链已发送: {filename}")
            return True
        else:
            await self.send_simple_msg(user_id, f"❌ 文件过大且 Alist 直链获取失败: {filename}")
            return False

    # =====================
    # WebSocket 接收（只用于接收，不用于发送）
    # =====================

    async def connect(self):
        """连接 NapCat WebSocket（仅用于接收消息）"""
        await self.get_bot_info()

        ws_url = config.NAPCAT_WS_URL
        # 如果 WebSocket 有 token，加到 URL
        if hasattr(config, 'NAPCAT_WS_TOKEN') and config.NAPCAT_WS_TOKEN:
            sep = '&' if '?' in ws_url else '?'
            ws_url = f"{ws_url}{sep}access_token={config.NAPCAT_WS_TOKEN}"

        try:
            print(f"🔌 连接 NapCat WebSocket: {config.NAPCAT_WS_URL}", flush=True)
            async with websockets.connect(ws_url) as ws:
                self.ws = ws
                print("✅ WebSocket 连接成功!", flush=True)
                async for message in ws:
                    await self.handle_message(message)
        except Exception as e:
            print(f"❌ WebSocket 错误: {e}", flush=True)
        finally:
            self.ws = None

    async def get_bot_info(self):
        """获取机器人 QQ 信息"""
        try:
            headers = {"Authorization": f"Bearer {config.NAPCAT_HTTP_TOKEN}"}
            response = requests.get(
                f"{config.NAPCAT_HTTP_URL}/get_login_info",
                headers=headers, timeout=10
            )
            data = response.json()
            if data.get('status') == 'ok':
                self.bot_qq = str(data['data']['user_id'])
                print(f"🤖 机器人 QQ: {self.bot_qq}")
        except Exception as e:
            print(f"⚠️ 获取 bot 信息失败: {e}")

    async def handle_message(self, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('post_type')
            message_type = data.get('message_type')

            if msg_type == 'message':
                if message_type == 'private':
                    await self.handle_private_message(data)
                elif message_type == 'group':
                    await self.handle_group_message(data)
        except Exception as e:
            print(f"消息处理异常: {e}")

    async def handle_private_message(self, data):
        """处理私聊消息"""
        user_id = str(data.get('user_id'))
        raw_message = data.get('raw_message', '')

        print(f"[私聊] from {user_id}: {raw_message[:80]}")

        # 权限检查
        if user_id != config.MASTER_QQ:
            return

        # 指令解析
        if raw_message.startswith('/录播 '):
            parts = raw_message.split(' ', 2)
            if len(parts) >= 3:
                url = parts[2]
                await self.send_reply(data, f"📥 收到录制任务: {url}")
                task_id = task_queue.submit_download(url, 'record')
                await self.send_reply(data, f"✅ 任务已提交: {task_id}")

        elif raw_message.startswith('/下载 ') or raw_message.startswith('下载 '):
            url = raw_message.split(' ', 1)[1].strip()
            if url:
                await self.send_reply(data, f"📥 收到下载任务: {url}")
                task_id = task_queue.submit_download(url, 'download')
                await self.send_reply(data, f"✅ 任务已提交: {task_id}")

        elif raw_message == '/任务' or raw_message == '查看任务':
            tasks = task_queue.get_all_tasks()
            reply = f"📋 当前任务 ({len(tasks)} 个):\n"
            for t in tasks[:5]:
                reply += f"- {t['task_id'][:8]} | {t['action']} | {t['status']} | {t['progress']}%\n"
            await self.send_reply(data, reply)

        else:
            # 包含关键词才走 LLM 解析
            keywords = ["下载", "录播", "截取", "剪辑", "提取音频", "转码", "合并", "http", "youtube", "bilibili"]
            if any(k in raw_message.lower() for k in keywords):
                await self.handle_llm_message(data, raw_message)

    async def handle_group_message(self, data):
        """处理群聊消息（只响应 @机器人）"""
        message = data.get('message', [])
        raw_message = data.get('raw_message', '')

        # 用 bot_qq 检查是否 @机器人
        check_qq = self.bot_qq or config.MASTER_QQ
        is_at_me = any(
            seg.get('type') == 'at' and str(seg.get('data', {}).get('qq', '')) == str(check_qq)
            for seg in message
        )
        if not is_at_me:
            return

        # 权限检查
        sender = data.get('sender', {})
        user_id = str(sender.get('user_id', ''))
        if user_id != config.MASTER_QQ:
            await self.send_group_reply(data, "抱歉，只有主人可以使用这个功能~")
            return

        text_content = ' '.join(
            seg.get('data', {}).get('text', '')
            for seg in message if seg.get('type') == 'text'
        ).strip()

        keywords = ["下载", "录播", "截取", "剪辑", "提取音频", "转码", "合并", "http", "youtube", "bilibili"]
        if any(k in text_content.lower() for k in keywords):
            await self.handle_llm_message(data, text_content)

    async def handle_llm_message(self, data, message):
        """使用 LLM 解析自然语言指令"""
        headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = (
            "你是指令解析器。从用户输入提取操作意图，输出 JSON:\n"
            '{"action": "download/record/transcode/cut/merge/extract_audio", '
            '"url": "视频链接（如有）", '
            '"input_file": "输入文件（如有）", '
            '"output_file": "输出文件（如有）"}\n\n'
            f"用户输入: {message}\n"
            "只输出 JSON，不要其他内容。"
        )

        try:
            resp = requests.post(
                config.LLM_API_URL,
                headers=headers,
                json={
                    "model": config.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是指令解析器，只输出JSON。"},
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=30
            )
            content = resp.json()['choices'][0]['message']['content']
            import re
            m = re.search(r'\{[^}]+\}', content, re.DOTALL)
            parsed = json.loads(m.group()) if m else {}

            action = parsed.get('action')
            if action in ('download', 'record') and parsed.get('url'):
                task_id = task_queue.submit_download(parsed['url'], action)
                await self.send_reply(data, f"✅ 任务已创建: {task_id}")
            elif action in ('transcode', 'cut', 'extract_audio') and parsed.get('input_file'):
                output = parsed.get('output_file', 'output.mp4')
                task_id = task_queue.submit_ffmpeg(action, parsed['input_file'], output)
                await self.send_reply(data, f"✅ 任务已创建: {task_id}")
            else:
                await self.send_reply(data, "❓ 无法解析指令，请明确说明操作（下载/录播）和链接。")

        except Exception as e:
            print(f"LLM 解析失败: {e}")
            await self.send_reply(data, f"❌ 解析失败: {e}")


# 全局实例
napcat_handler = NapcatHandler()


async def start_napcat_listener():
    """启动 Napcat 监听器（断线自动重连）"""
    while True:
        try:
            await napcat_handler.connect()
        except Exception as e:
            print(f"Reconnecting in 5s: {e}")
        await asyncio.sleep(5)

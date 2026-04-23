# Video Bot 逻辑表 & 需求文档

> 最后更新: 2026-03-23  
> 生产路径: Homeserver `~/video-bot/app/`  
> PM2 ID: 7 (`video-bot`)  
> 本地代码: `napcat-ytdlp/` (公开版) / `napcat-ytdlp-personal/` (个人版)

---

## 一、架构概览

```
┌─────────────┐     WebSocket (3003)     ┌──────────────────┐
│  NapCat v13  │ ◄──────────────────────► │   video-bot      │
│  (Docker)    │     HTTP API (3002)      │   (Python/Flask) │
│  QQ: 1873.. │ ◄──────────────────────── │   PM2 id:7       │
└─────────────┘                           └──────┬───────────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                              yt-dlp/FFmpeg   Alist API    MiniMax LLM
                              (下载/转码)    (文件直链)    (自然语言解析)
```

**通信方式:**
- **接收消息**: WebSocket (`ws://127.0.0.1:3003`)
- **发送消息**: HTTP API (`http://127.0.0.1:3002`, token: `NAPCAT_HTTP_TOKEN`)

---

## 二、配置项

| 配置项 | 生产值 | 说明 |
|--------|--------|------|
| `MASTER_QQ` | `314389463` | 主人QQ（私聊权限验证） |
| `BOT_QQ` | `1873755396` | 机器人QQ（群聊@识别） |
| `FLASK_PORT` | `5000` | Web管理面板端口 |
| `DOWNLOAD_DIR` | `/vol1/downloads` | 下载目录（飞牛OS存储） |
| `COOKIES_FILE` | `~/video-bot/cookies.txt` | YouTube cookies |
| `ALIST_URL` | `http://192.168.3.11:5244` | Alist API |
| `NAPCAT_WS_URL` | `ws://127.0.0.1:3003` | NapCat WS (容器3001→宿主3003) |
| `NAPCAT_HTTP_URL` | `http://127.0.0.1:3002` | NapCat HTTP (容器3000→宿主3002) |
| `LLM_MODEL` | `MiniMax-M2.5` | LLM 模型 |
| `MAX_CONCURRENT_TASKS` | `2` | 最大并发任务数 |

---

## 三、消息处理逻辑表

### 3.1 消息入口 (`handle_message`)

```
收到 WebSocket 消息
  ├─ post_type == "message"
  │   ├─ message_type == "private" → handle_private_message()
  │   └─ message_type == "group"  → handle_group_message()
  └─ 其他 (meta_event, notice) → 忽略
```

### 3.2 私聊消息 (`handle_private_message`)

| 步骤 | 条件 | 动作 | 备注 |
|------|------|------|------|
| 1 | `user_id != MASTER_QQ` | 静默忽略 | **仅主人可用私聊** |
| 2 | 消息匹配 `/录播` 或 `录播` + URL | 提交 record 任务 | 支持 `实时` 关键词 |
| 3 | 消息匹配 `/下载` 或 `下载` + URL | 提交 download 任务 | 正则提取URL |
| 4 | 消息 == `/任务` 或 `查看任务` | 返回任务列表（前5个） | |
| 5 | 消息匹配 `/停止` + 任务ID | 停止指定任务 | 18位hex ID |
| 6 | 消息含关键词 | → `handle_llm_message()` | LLM 自然语言解析 |
| 7 | 以上都不匹配 | 静默忽略 | 不响应闲聊 |

**关键词列表:** `下载, 录播, 截取, 剪辑, 提取音频, 转码, 合并, http, youtube, bilibili`

### 3.3 群聊消息 (`handle_group_message`)

| 步骤 | 条件 | 动作 | 备注 |
|------|------|------|------|
| 1 | 未 @机器人 (`BOT_QQ`) | 静默忽略 | 必须 @bot 才触发 |
| 2 | 已 @机器人 | 提取纯文本内容 | 去掉 @段落 |
| 3 | 文本含关键词 | → `handle_llm_message()` | 所有人可用 |
| 4 | 文本无关键词 | 静默忽略 | |

### 3.4 LLM 解析 (`handle_llm_message`)

| 步骤 | 说明 |
|------|------|
| 1 | 构造 prompt，要求 LLM 输出 JSON |
| 2 | 调用 MiniMax M2.5 API (timeout 30s) |
| 3 | 正则提取 JSON `{...}` |
| 4 | 根据 `action` 分发: download/record → `submit_download()`, transcode/cut/extract_audio → `submit_ffmpeg()` |
| 5 | 解析失败 → 返回错误提示 |

**LLM 输出格式:**
```json
{
  "action": "download/record/transcode/cut/merge/extract_audio",
  "url": "视频链接",
  "input_file": "输入文件",
  "output_file": "输出文件"
}
```

---

## 四、文件发送逻辑 (`send_file`)

```
文件大小判断
  ├─ < 100MB (小文件)
  │   ├─ 媒体类型 (mp3/mp4/jpg...) → 发 CQ 码 + 上传文件
  │   └─ 上传失败 → fallback 到 Alist 直链
  └─ >= 100MB (大文件)
      └─ 直接走 Alist 直链
```

**Alist 直链获取流程:**
1. 登录 Alist API 获取 token
2. 调用 `/api/fs/get` 获取 `raw_url`
3. 如果无 `raw_url`（本地存储），拼接公网代理链接 + sign

---

## 五、权限模型

| 场景 | 谁可以用 | 实现方式 |
|------|----------|----------|
| **私聊** | 仅 MASTER_QQ (`314389463`) | 代码硬检查 `user_id != MASTER_QQ` |
| **群聊 @bot** | **所有人** | 只检查是否 @BOT_QQ，无权限限制 |
| **Web 面板** | 任何能访问 5000 端口的人 | 无认证（局域网） |

> ⚠️ 2026-03-23 修改: 群聊从「仅主人」改为「所有人可用」。  
> 同时修复: @检测从 `MASTER_QQ` 改为 `BOT_QQ`。

---

## 六、Web API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端管理页面 |
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建任务 (JSON body) |
| GET | `/api/tasks/<id>` | 获取任务详情 |
| DELETE | `/api/tasks/<id>` | 删除/停止任务 |
| GET | `/api/logs/<id>` | 任务日志 (SSE) |
| GET | `/events` | 实时进度 (SSE) |

---

## 七、需求清单 & 变更记录

### 当前需求状态

| # | 需求 | 状态 | 说明 |
|---|------|------|------|
| R1 | 私聊指令控制（下载/录播/任务/停止） | ✅ 已实现 | 仅主人 |
| R2 | 群聊 @bot 触发 LLM 解析下载 | ✅ 已实现 | 所有人可用 (2026-03-23) |
| R3 | LLM 自然语言指令解析 | ✅ 已实现 | MiniMax M2.5 |
| R4 | 小文件直传 QQ / 大文件 Alist 直链 | ✅ 已实现 | 阈值 100MB |
| R5 | 实时录播支持 | ✅ 已实现 | `实时` 关键词 |
| R6 | Web 管理面板 | ✅ 已实现 | Flask port 5000 |
| R7 | 断线自动重连 | ✅ 已实现 | 5s 间隔 |

### 变更记录

| 日期 | 变更 | 原因 |
|------|------|------|
| 2026-03-23 | 群聊权限: 仅主人 → 所有人可用 | 群友需要使用 |
| 2026-03-23 | @检测: `MASTER_QQ` → `BOT_QQ` | Bug: @bot无反应，@主人才触发 |
| 2026-03-23 | 进程管理: nohup → PM2 (id:7) | 便于管理、自动重启 |

---

## 八、已知问题 & 待改进

| # | 问题 | 优先级 | 备注 |
|---|------|--------|------|
| 1 | 本地代码 (`napcat-ytdlp/config.py`) 无 `BOT_QQ` 变量 | 中 | 生产有，本地没有 |
| 2 | 群聊无速率限制 | 低 | 目前群不大，暂不需要 |
| 3 | Web 面板无认证 | 低 | 仅局域网访问 |
| 4 | 群聊回复用 `send_reply`（私聊方法）而非 `send_group_reply` | 中 | LLM解析结果回复到私聊而非群 |

"""
Sandbox server for local bot testing without Telegram.

Two modes:
  1. With bot process (two terminals):
     Terminal 1: python -m sandbox.server
     Terminal 2: SANDBOX_MODE=1 python bot.py
  2. Standalone (one process, no Telegram):
     SANDBOX_STANDALONE=1 python -m sandbox.server

Then open http://localhost:8888 in your browser.
"""

import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

# ── Config ────────────────────────────────────────────────────────────────────
SANDBOX_PORT = int(os.getenv("SANDBOX_PORT", "8888"))
FAKE_CHAT_ID = 100000001
FAKE_USER_ID = 200000001
FAKE_BOT_ID  = 300000001

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("sandbox")

# ── Shared state ──────────────────────────────────────────────────────────────
# asyncio.Queue must be created inside the running event loop (Python 3.9
# compatibility — Queue captured the loop at construction time in 3.9).
# We initialise it in the lifespan handler, not at import time.
_update_queue: Optional[asyncio.Queue] = None


@asynccontextmanager
async def _lifespan(_: FastAPI):
    global _update_queue, _bot_connected
    _update_queue = asyncio.Queue()
    if os.getenv('SANDBOX_STANDALONE'):
        _bot_connected = True
        logger.info('[SANDBOX] standalone mode — brain runs in-process')
    yield


app = FastAPI(title="Bot Sandbox", lifespan=_lifespan)
_update_counter: int = 1
_ws_clients: List[WebSocket] = []
_files: Dict[str, str] = {}          # file_id → local path
_message_counter: int = 1000         # fake message_id counter
_bot_connected: bool = False         # True once the bot calls getMe
_standalone_last_message_id: Optional[int] = None  # for EditMessage in standalone mode


# ── Helpers ───────────────────────────────────────────────────────────────────
def _next_uid() -> int:
    global _update_counter
    v = _update_counter
    _update_counter += 1
    return v


def _next_mid() -> int:
    global _message_counter
    v = _message_counter
    _message_counter += 1
    return v


async def _parse_body(request: Request) -> Dict:
    """Parse a Telegram Bot API request body.

    python-telegram-bot v21 sends ALL non-file requests as
    application/x-www-form-urlencoded, not JSON.  Nested objects
    (reply_markup, allowed_updates …) are JSON-encoded strings inside
    the form fields, so we decode those too.
    """
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}

    # URL-encoded form body (PTB default)
    try:
        form = await request.form()
    except Exception:
        return {}

    result: Dict = {}
    for k, v in form.items():
        # Decode JSON-encoded values (dicts, lists)
        if isinstance(v, str) and v and v[0] in ("{", "["):
            try:
                result[k] = json.loads(v)
                continue
            except json.JSONDecodeError:
                pass
        result[k] = v
    return result


async def _broadcast(event: Dict[str, Any]) -> None:
    dead = []
    text = json.dumps(event, ensure_ascii=False)
    for ws in list(_ws_clients):
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


def _fake_user() -> Dict:
    return {
        "id": FAKE_USER_ID,
        "is_bot": False,
        "first_name": "Sandbox",
        "last_name": "User",
        "username": "sandbox_user",
    }


def _fake_chat() -> Dict:
    return {
        "id": FAKE_CHAT_ID,
        "type": "private",
        "first_name": "Sandbox",
        "username": "sandbox_user",
    }


def _make_message_update(text: str) -> Dict:
    return {
        "update_id": _next_uid(),
        "message": {
            "message_id": _next_mid(),
            "from": _fake_user(),
            "chat": _fake_chat(),
            "date": int(time.time()),
            "text": text,
        },
    }


def _make_callback_update(callback_data: str, orig_message_id: int) -> Dict:
    return {
        "update_id": _next_uid(),
        "callback_query": {
            "id": str(uuid.uuid4()),
            "from": _fake_user(),
            "message": {
                "message_id": orig_message_id,
                "from": {"id": FAKE_BOT_ID, "is_bot": True, "first_name": "Sandbox Bot", "username": "sandbox_bot"},
                "chat": _fake_chat(),
                "date": int(time.time()),
                "text": "...",
            },
            "chat_instance": str(FAKE_CHAT_ID),
            "data": callback_data,
        },
    }


def _make_document_update(file_id: str, filename: str, file_size: int) -> Dict:
    """Fake update: user sent a document (e.g. from URL)."""
    return {
        "update_id": _next_uid(),
        "message": {
            "message_id": _next_mid(),
            "from": _fake_user(),
            "chat": _fake_chat(),
            "date": int(time.time()),
            "document": {
                "file_id": file_id,
                "file_unique_id": file_id,
                "file_name": filename,
                "file_size": file_size,
            },
        },
    }


# ── Fake Telegram Bot API ─────────────────────────────────────────────────────

async def _mark_bot_connected() -> None:
    global _bot_connected
    if not _bot_connected:
        _bot_connected = True
        logger.info("[SANDBOX] bot connected")
        await _broadcast({"type": "bot_status", "online": True})
        await _broadcast({"type": "log", "level": "success", "message": "🤖 Bot connected to sandbox"})


@app.api_route("/bot{token}/getMe", methods=["GET", "POST"])
async def get_me(token: str):
    await _mark_bot_connected()
    return {
        "ok": True,
        "result": {
            "id": FAKE_BOT_ID,
            "is_bot": True,
            "first_name": "Sandbox Bot",
            "username": "sandbox_bot",
            "can_join_groups": False,
            "can_read_all_group_messages": False,
            "supports_inline_queries": False,
        },
    }


@app.api_route("/bot{token}/getWebhookInfo", methods=["GET", "POST"])
async def get_webhook_info(token: str):
    return {"ok": True, "result": {"url": "", "has_custom_certificate": False, "pending_update_count": 0}}


@app.api_route("/bot{token}/deleteWebhook", methods=["GET", "POST"])
async def delete_webhook(token: str):
    return {"ok": True, "result": True}


@app.api_route("/bot{token}/setMyCommands", methods=["GET", "POST"])
async def set_my_commands(token: str):
    return {"ok": True, "result": True}


@app.api_route("/bot{token}/getUpdates", methods=["GET", "POST"])
async def get_updates(token: str, request: Request):
    """Long-polling endpoint — blocks until an update is available or timeout expires."""
    body = await _parse_body(request)
    timeout = max(float(body.get("timeout", 0)), 1.0)

    try:
        update = await asyncio.wait_for(_update_queue.get(), timeout=timeout)
        await _broadcast({
            "type": "log",
            "level": "debug",
            "message": f"📨 Update #{update['update_id']} dispatched to bot",
        })
        return {"ok": True, "result": [update]}
    except asyncio.TimeoutError:
        return {"ok": True, "result": []}


@app.api_route("/bot{token}/sendMessage", methods=["GET", "POST"])
async def send_message(token: str, request: Request):
    body = await _parse_body(request)
    text = body.get("text", "")
    reply_markup = body.get("reply_markup")  # dict or None
    mid = _next_mid()

    await _broadcast({
        "type": "bot_message",
        "message_id": mid,
        "text": text,
        "parse_mode": body.get("parse_mode", ""),
        "reply_markup": reply_markup,
    })
    await _broadcast({
        "type": "log",
        "level": "success",
        "message": f"🤖 sendMessage → {text[:80]}{'…' if len(text) > 80 else ''}",
    })

    return {
        "ok": True,
        "result": {
            "message_id": mid,
            "chat": _fake_chat(),
            "date": int(time.time()),
            "text": text,
        },
    }


@app.api_route("/bot{token}/editMessageText", methods=["GET", "POST"])
async def edit_message_text(token: str, request: Request):
    body = await _parse_body(request)
    text = body.get("text", "")
    mid = body.get("message_id", _next_mid())
    reply_markup = body.get("reply_markup")

    await _broadcast({
        "type": "bot_edit_message",
        "message_id": mid,
        "text": text,
        "parse_mode": body.get("parse_mode", ""),
        "reply_markup": reply_markup,
    })
    await _broadcast({
        "type": "log",
        "level": "success",
        "message": f"🤖 editMessageText #{mid} → {text[:80]}{'…' if len(text) > 80 else ''}",
    })

    return {
        "ok": True,
        "result": {
            "message_id": mid,
            "chat": _fake_chat(),
            "date": int(time.time()),
            "text": text,
        },
    }


@app.api_route("/bot{token}/editMessageReplyMarkup", methods=["GET", "POST"])
async def edit_message_reply_markup(token: str, request: Request):
    body: Dict = {}
    try:
        body = await request.json()
    except Exception:
        pass

    mid = body.get("message_id", 0)
    reply_markup = body.get("reply_markup")

    await _broadcast({
        "type": "bot_edit_keyboard",
        "message_id": mid,
        "reply_markup": reply_markup,
    })

    return {"ok": True, "result": True}


@app.api_route("/bot{token}/answerCallbackQuery", methods=["GET", "POST"])
async def answer_callback_query(token: str, request: Request):
    return {"ok": True, "result": True}


@app.api_route("/bot{token}/sendDocument", methods=["GET", "POST"])
async def send_document(token: str, request: Request):
    form = await request.form()

    caption: str = form.get("caption", "") or ""
    document = form.get("document")

    file_id = str(uuid.uuid4())
    filename = "document"
    file_size = 0

    if document and hasattr(document, "filename"):
        filename = document.filename or "document"
        content = await document.read()
        file_size = len(content)
        save_path = f"/tmp/sandbox_{file_id}_{filename}"
        with open(save_path, "wb") as fh:
            fh.write(content)
        _files[file_id] = save_path
        logger.info("[SANDBOX] sendDocument: %s (%d bytes)", filename, file_size)

    mid = _next_mid()
    await _broadcast({
        "type": "bot_document",
        "message_id": mid,
        "filename": filename,
        "caption": caption,
        "file_id": file_id,
        "file_size": file_size,
        "download_url": f"/sandbox/download/{file_id}/{filename}",
    })
    await _broadcast({
        "type": "log",
        "level": "success",
        "message": f"📄 sendDocument → {filename} ({file_size:,} bytes)",
    })

    return {
        "ok": True,
        "result": {
            "message_id": mid,
            "document": {
                "file_id": file_id,
                "file_unique_id": file_id,
                "file_name": filename,
                "file_size": file_size,
            },
        },
    }


@app.api_route("/bot{token}/deleteMessage", methods=["GET", "POST"])
async def delete_message(token: str, request: Request):
    return {"ok": True, "result": True}


@app.api_route("/bot{token}/getFile", methods=["GET", "POST"])
async def get_file(token: str, request: Request):
    body: Dict = {}
    try:
        body = await request.json()
    except Exception:
        pass
    fid = body.get("file_id", "")
    return {"ok": True, "result": {"file_id": fid, "file_unique_id": fid, "file_size": 0, "file_path": f"documents/{fid}"}}


# ── Standalone: run brain in-process (no bot process) ────────────────────────
def _run_standalone_brain(event: Dict) -> List[Any]:
    """Call the core brain and return list of response objects."""
    from core.brain import process
    return process(FAKE_CHAT_ID, event)


async def _apply_standalone_responses(
    responses: List[Any],
    callback_message_id: Optional[int] = None,
) -> None:
    """Broadcast brain responses to WebSocket clients."""
    global _standalone_last_message_id
    edit_mid = callback_message_id
    for r in responses:
        rtype = type(r).__name__
        if rtype == 'AnswerCallback':
            continue
        if rtype == 'ReplyText':
            mid = _next_mid()
            _standalone_last_message_id = mid
            rm = getattr(r, 'reply_markup', None)
            await _broadcast({
                'type': 'bot_message',
                'message_id': mid,
                'text': r.text,
                'parse_mode': getattr(r, 'parse_mode', '') or '',
                'reply_markup': {'inline_keyboard': rm} if rm else None,
            })
            await _broadcast({
                'type': 'log',
                'level': 'success',
                'message': f"🤖 → {r.text[:80]}{'…' if len(r.text) > 80 else ''}",
            })
            continue
        if rtype == 'EditMessage':
            mid = getattr(r, 'message_id', None) or edit_mid or _standalone_last_message_id
            if mid is not None:
                rm = getattr(r, 'reply_markup', None)
                await _broadcast({
                    'type': 'bot_edit_message',
                    'message_id': mid,
                    'text': r.text,
                    'parse_mode': getattr(r, 'parse_mode', '') or '',
                    'reply_markup': {'inline_keyboard': rm} if rm else None,
                })
                await _broadcast({
                    'type': 'log',
                    'level': 'success',
                    'message': f"🤖 (edit) → {r.text[:80]}{'…' if len(r.text) > 80 else ''}",
                })
            if edit_mid is not None:
                edit_mid = None
            continue
        if rtype == 'SendDocument':
            file_id = str(uuid.uuid4())
            src = getattr(r, 'file_path', '')
            filename = getattr(r, 'filename', 'document')
            if os.path.exists(src):
                dest = f'/tmp/sandbox_{file_id}_{filename}'
                shutil.copy2(src, dest)
                _files[file_id] = dest
            mid = _next_mid()
            download_url = f'/sandbox/download/{file_id}/{filename}'
            await _broadcast({
                'type': 'bot_document',
                'message_id': mid,
                'filename': filename,
                'caption': getattr(r, 'caption', '') or '',
                'file_id': file_id,
                'file_size': os.path.getsize(src) if os.path.exists(src) else 0,
                'download_url': download_url,
            })
            await _broadcast({'type': 'log', 'level': 'success', 'message': f'📄 → {filename}'})


# ── Sandbox control endpoints (called by the web UI) ─────────────────────────

@app.post("/sandbox/send_message")
async def sandbox_send_message(request: Request):
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)

    await _broadcast({"type": "user_message", "text": text})
    await _broadcast({"type": "log", "level": "info", "message": f"👤 User → {text}"})

    if os.getenv("SANDBOX_STANDALONE"):
        event = {"type": "message", "text": text}
        responses = _run_standalone_brain(event)
        await _apply_standalone_responses(responses)
    else:
        update = _make_message_update(text)
        await _update_queue.put(update)

    return {"ok": True}


@app.post("/sandbox/send_command")
async def sandbox_send_command(request: Request):
    body = await request.json()
    cmd = body.get("command", "/start")

    await _broadcast({"type": "user_message", "text": cmd, "is_command": True})
    await _broadcast({"type": "log", "level": "info", "message": f"⚡ Command → {cmd}"})

    if os.getenv("SANDBOX_STANDALONE"):
        event = {"type": "message", "text": cmd}
        responses = _run_standalone_brain(event)
        await _apply_standalone_responses(responses)
    else:
        update = _make_message_update(cmd)
        await _update_queue.put(update)

    return {"ok": True}


@app.post("/sandbox/click_button")
async def sandbox_click_button(request: Request):
    body = await request.json()
    callback_data: str = body.get("callback_data", "")
    button_text: str = body.get("button_text", callback_data)
    orig_message_id: int = body.get("message_id", _message_counter)

    await _broadcast({"type": "user_button_click", "button_text": button_text, "callback_data": callback_data})
    await _broadcast({"type": "log", "level": "info", "message": f"🔘 Button → [{button_text}] data={callback_data}"})

    if os.getenv("SANDBOX_STANDALONE"):
        event = {"type": "callback", "data": callback_data, "message_id": orig_message_id}
        responses = _run_standalone_brain(event)
        await _apply_standalone_responses(responses, callback_message_id=orig_message_id)
    else:
        update = _make_callback_update(callback_data, orig_message_id)
        await _update_queue.put(update)

    return {"ok": True}


@app.post("/sandbox/send_document")
async def sandbox_send_document(request: Request):
    """Simulate user sending a file (e.g. from URL). Body: {"url": "https://..."} or {"filename": "x.pdf"}."""
    body = await request.json()
    url = (body.get("url") or "").strip()
    filename = (body.get("filename") or "").strip() or "document.pdf"

    if not url:
        return JSONResponse({"ok": False, "error": "url required"}, status_code=400)

    file_id = str(uuid.uuid4())
    file_size = 0
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "SandboxBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            file_size = len(content)
            name_from_url = url.split("/")[-1].split("?")[0]
            if name_from_url:
                filename = name_from_url
            dest = f"/tmp/sandbox_{file_id}_{filename}"
            with open(dest, "wb") as f:
                f.write(content)
            _files[file_id] = dest
    except Exception as e:
        logger.warning("[SANDBOX] send_document URL fetch failed: %s", e)
        filename = filename or "document"

    await _broadcast({"type": "user_message", "text": f"📎 File: {filename}", "is_file": True})
    await _broadcast({"type": "log", "level": "info", "message": f"📎 User → file: {filename}"})

    if os.getenv("SANDBOX_STANDALONE"):
        await _broadcast({
            "type": "bot_message",
            "message_id": _next_mid(),
            "text": "دریافت فایل در این ربات در حال حاضر پشتیبانی نمی‌شود. لطفاً از متن و دکمه‌ها استفاده کنید.",
        })
        await _broadcast({"type": "log", "level": "success", "message": "🤖 → (file not handled in flow)"})
    else:
        update = _make_document_update(file_id, filename, file_size)
        await _update_queue.put(update)

    return {"ok": True, "file_id": file_id, "filename": filename}


@app.post("/sandbox/clear_queue")
async def sandbox_clear_queue():
    drained = 0
    while not _update_queue.empty():
        try:
            _update_queue.get_nowait()
            drained += 1
        except asyncio.QueueEmpty:
            break
    return {"ok": True, "drained": drained}


@app.get("/sandbox/download/{file_id}/{filename}")
async def sandbox_download(file_id: str, filename: str):
    path = _files.get(file_id)
    if not path or not os.path.exists(path):
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, filename=filename)


# ── WebSocket (browser ↔ server real-time events) ────────────────────────────

@app.websocket("/sandbox/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    logger.info("[SANDBOX] browser connected (total=%d)", len(_ws_clients))

    await ws.send_text(json.dumps({
        "type": "log",
        "level": "info",
        "message": "🟢 Sandbox ready — click /start to begin",
    }))
    await ws.send_text(json.dumps({"type": "connected"}))
    # Tell the new client the current bot connection state
    await ws.send_text(json.dumps({"type": "bot_status", "online": _bot_connected}))

    try:
        while True:
            await ws.receive_text()   # keep-alive; UI doesn't send over WS
    except WebSocketDisconnect:
        if ws in _ws_clients:
            _ws_clients.remove(ws)
        logger.info("[SANDBOX] browser disconnected (total=%d)", len(_ws_clients))


# ── Web UI ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    return FileResponse(Path(__file__).parent / "index.html")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SANDBOX_PORT, log_level="info")

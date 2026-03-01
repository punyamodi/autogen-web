import asyncio
import json
import queue
import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..agents.base import AgentRunner
from ..core.database import ChatMessage, ChatSession, get_db
from ..core.schemas import LLMConfig
from ..core.settings import settings

router = APIRouter()

_active_runners: Dict[str, AgentRunner] = {}


def _build_llm_config(cfg: LLMConfig) -> dict:
    return {
        "seed": 42,
        "config_list": [
            {
                "model": cfg.model,
                "base_url": cfg.base_url,
                "api_type": "open_ai",
                "api_key": cfg.api_key,
            }
        ],
        "temperature": cfg.temperature,
        "timeout": cfg.timeout,
    }


def _default_llm_config() -> dict:
    return _build_llm_config(
        LLMConfig(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
        )
    )


def _save_message(
    db: Session,
    session_id: str,
    sender: str,
    content: str,
    msg_type: str = "agent_message",
    recipient: str = None,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        sender=sender,
        recipient=recipient,
        content=content,
        msg_type=msg_type,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    session_row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session_row:
        session_row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        session_row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session_row:
            await websocket.send_json({"type": "error", "content": "Session not found."})
            await websocket.close()
            return

        await websocket.send_json({"type": "connected", "session_id": session_id})

        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "message":
                user_content = data.get("content", "").strip()
                if not user_content:
                    continue

                mode = data.get("mode", session_row.mode)
                raw_config = data.get("config")
                if raw_config:
                    llm_cfg = LLMConfig(**raw_config)
                    llm_config = _build_llm_config(llm_cfg)
                else:
                    llm_config = _default_llm_config()

                _save_message(db, session_id, "User", user_content, "user_message")

                await websocket.send_json({"type": "thinking", "content": "Agents are working..."})

                runner = AgentRunner(mode, llm_config)
                _active_runners[session_id] = runner
                runner.start(user_content)

                loop = asyncio.get_event_loop()
                accumulated: list[dict] = []

                while True:
                    try:
                        msg = await loop.run_in_executor(
                            None,
                            lambda: runner.capture_queue.get(timeout=120),
                        )
                    except queue.Empty:
                        await websocket.send_json(
                            {"type": "error", "content": "Agent response timed out."}
                        )
                        break

                    if msg["type"] == "agent_message":
                        accumulated.append(msg)
                        await websocket.send_json(msg)

                    elif msg["type"] == "error":
                        await websocket.send_json(msg)
                        break

                    elif msg["type"] == "done":
                        for m in accumulated:
                            _save_message(
                                db,
                                session_id,
                                m.get("sender", "Agent"),
                                m.get("content", ""),
                                "agent_message",
                            )
                        await websocket.send_json({"type": "done"})
                        break

                if session_id in _active_runners:
                    del _active_runners[session_id]

    except WebSocketDisconnect:
        pass
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        db.close()
        _active_runners.pop(session_id, None)

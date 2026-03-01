import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import ChatMessage, ChatSession, get_db
from ..core.schemas import (
    ExportResponse,
    MessageResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    row = ChatSession(
        id=str(uuid.uuid4()),
        name=payload.name,
        mode=payload.mode,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    return row


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(session_id: str, payload: SessionUpdate, db: Session = Depends(get_db)):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    if payload.name is not None:
        row.name = payload.name
    if payload.mode is not None:
        row.mode = payload.mode
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(row)
    db.commit()


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.get("/{session_id}/export", response_model=ExportResponse)
def export_session(session_id: str, db: Session = Depends(get_db)):
    row = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return ExportResponse(
        session_id=row.id,
        session_name=row.name,
        mode=row.mode,
        messages=messages,
        exported_at=datetime.utcnow(),
    )

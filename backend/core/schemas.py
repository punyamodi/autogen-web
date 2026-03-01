from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "NULL"
    model: str = "local-model"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    timeout: int = Field(default=600, ge=30)


class SessionCreate(BaseModel):
    name: str = "New Chat"
    mode: str = "pair_coder"


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    mode: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    name: str
    mode: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    recipient: Optional[str]
    content: str
    msg_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WSIncoming(BaseModel):
    type: str
    content: Optional[str] = None
    mode: Optional[str] = None
    config: Optional[LLMConfig] = None


class AgentModeInfo(BaseModel):
    id: str
    name: str
    description: str
    agents: List[str]
    icon: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_reachable: bool
    llm_base_url: str


class ExportResponse(BaseModel):
    session_id: str
    session_name: str
    mode: str
    messages: List[MessageResponse]
    exported_at: datetime

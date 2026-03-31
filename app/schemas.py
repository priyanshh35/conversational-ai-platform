from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# User
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    profile: Optional[dict] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    profile: Optional[dict] = None


class UserOut(BaseModel):
    id: str
    username: str
    email: Optional[str]
    profile: dict
    created_at: datetime

    class Config:
        from_attributes = True


# Conversation
class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None


class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_turns: int
    summary: Optional[str]

    class Config:
        from_attributes = True


# MessagEs
class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    rag_hit: bool
    response_latency: Optional[float]
    sentiment_score: Optional[float]
    is_repair_turn: bool

    class Config:
        from_attributes = True


# Chat
class ChatRequest(BaseModel):
    conversation_id: str
    user_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    rag_hit: bool
    rag_sources: List[str]
    latency_seconds: float
    repair_detected: bool


# Analytics
class ConversationAnalytics(BaseModel):
    conversation_id: str
    total_turns: int
    avg_latency: float
    rag_hit_rate: float
    repair_rate: float
    avg_sentiment: float


class GlobalAnalytics(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    avg_latency: float
    rag_hit_rate: float
    repair_rate: float
    avg_sentiment: float
    avg_session_length: float
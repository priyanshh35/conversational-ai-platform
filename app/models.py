import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = Column(JSON, default=lambda: {
        "tone": "neutral",           # formal | casual | neutral
        "verbosity": "medium",       # brief | medium | detailed
        "topics_of_interest": [],
        "expertise_level": "intermediate",  # beginner | intermediate | expert
        "preferred_language": "en"
    })

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Rolling summary of older turns (when history > MAX_HISTORY_TURNS)
    summary = Column(Text, nullable=True)

    # Metadata
    total_turns = Column(Integer, default=0)
    avg_response_latency = Column(Float, default=0.0)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # RAG metadata
    rag_chunks_used = Column(JSON, nullable=True)    
    rag_hit = Column(Boolean, default=False)          

    # Quality signals
    response_latency = Column(Float, nullable=True)  
    sentiment_score = Column(Float, nullable=True)   
    is_repair_turn = Column(Boolean, default=False)  # user corrected the bot

    conversation = relationship("Conversation", back_populates="messages")
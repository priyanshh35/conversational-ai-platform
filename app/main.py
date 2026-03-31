from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import engine, get_db, Base
from app.models import User, Conversation, Message
from app.schemas import (
    UserCreate, UserUpdate, UserOut,
    ConversationCreate, ConversationOut, MessageOut,
    ChatRequest, ChatResponse,
    ConversationAnalytics, GlobalAnalytics
)
from app.llm import chat_completion
from app.rag import retrieve_and_rerank
from app.conversation import (
    get_conversation_history, detect_repair,
    compute_sentiment, update_conversation_stats
)
from app.personalization import build_system_prompt, update_profile
from app.analytics import get_conversation_analytics, get_global_analytics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conversational AI Platform",
    description="FastAPI-powered conversational AI with RAG, personalization, and analytics",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/users", response_model=UserOut, tags=["Users"])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        profile=payload.profile or {
            "tone": "neutral", "verbosity": "medium",
            "topics_of_interest": [], "expertise_level": "intermediate"
        }
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/users/{user_id}/profile", response_model=UserOut, tags=["Users"])
def update_user_profile(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.profile:
        update_profile(db, user_id, payload.profile)
    if payload.email:
        user.email = payload.email
        db.commit()
    db.refresh(user)
    return user


@app.post("/conversations", response_model=ConversationOut, tags=["Conversations"])
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conv = Conversation(
        user_id=payload.user_id,
        title=payload.title or "New Conversation"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@app.get("/conversations/{conversation_id}", response_model=ConversationOut, tags=["Conversations"])
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.get("/users/{user_id}/conversations", response_model=List[ConversationOut], tags=["Conversations"])
def list_user_conversations(user_id: str, db: Session = Depends(get_db)):
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()


@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut], tags=["Conversations"])
def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )


@app.delete("/conversations/{conversation_id}", tags=["Conversations"])
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.is_active = False
    db.commit()
    return {"message": "Conversation archived"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # 1. Validate conversation and user
    conv = db.query(Conversation).filter(
        Conversation.id == payload.conversation_id,
        Conversation.is_active == True
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or inactive")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Detect repair intent
    is_repair = detect_repair(payload.message)
    user_sentiment = compute_sentiment(payload.message)

    # 3. RAG retrieval
    rag_results = retrieve_and_rerank(payload.message)
    rag_hit = len(rag_results) > 0
    rag_context = "\n\n".join([r["text"] for r in rag_results])
    rag_sources = [r["metadata"].get("category", "general") for r in rag_results]

    # 4. Build personalized system prompt
    system_prompt = build_system_prompt(user, rag_context=rag_context)

    # 5. Get conversation history (with sliding window / summarization)
    history = get_conversation_history(db, payload.conversation_id)

    # 6. Build full message list for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    llm_messages += history
    llm_messages.append({"role": "user", "content": payload.message})

    # 7. Call LLM
    response_text, latency = chat_completion(llm_messages)

    # 8. Persist user message
    user_msg = Message(
        conversation_id=payload.conversation_id,
        role="user",
        content=payload.message,
        sentiment_score=user_sentiment,
        is_repair_turn=is_repair
    )
    db.add(user_msg)

    # 9. Persist assistant message
    assistant_msg = Message(
        conversation_id=payload.conversation_id,
        role="assistant",
        content=response_text,
        rag_hit=rag_hit,
        rag_chunks_used=rag_sources,
        response_latency=latency,
        sentiment_score=compute_sentiment(response_text)
    )
    db.add(assistant_msg)
    db.commit()

    # 10. Update conversation-level stats
    update_conversation_stats(db, payload.conversation_id, latency)

    return ChatResponse(
        conversation_id=payload.conversation_id,
        message_id=assistant_msg.id,
        response=response_text,
        rag_hit=rag_hit,
        rag_sources=rag_sources,
        latency_seconds=round(latency, 3),
        repair_detected=is_repair
    )


@app.get("/analytics/conversation/{conversation_id}",
         response_model=ConversationAnalytics, tags=["Analytics"])
def conversation_analytics(conversation_id: str, db: Session = Depends(get_db)):
    return get_conversation_analytics(db, conversation_id)


@app.get("/analytics/global", response_model=GlobalAnalytics, tags=["Analytics"])
def global_analytics(db: Session = Depends(get_db)):
    return get_global_analytics(db)
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, Conversation, Message
from app.schemas import ConversationAnalytics, GlobalAnalytics


def get_conversation_analytics(db: Session, conversation_id: str) -> ConversationAnalytics:
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).all()

    assistant_msgs = [m for m in messages if m.role == "assistant"]
    total_turns = len(assistant_msgs)

    avg_latency = (
        sum(m.response_latency for m in assistant_msgs if m.response_latency)
        / max(len([m for m in assistant_msgs if m.response_latency]), 1)
    )

    rag_hits = sum(1 for m in assistant_msgs if m.rag_hit)
    rag_hit_rate = round(rag_hits / max(total_turns, 1), 2)

    repair_turns = sum(1 for m in messages if m.is_repair_turn)
    repair_rate = round(repair_turns / max(len(messages), 1), 2)

    sentiments = [m.sentiment_score for m in messages if m.sentiment_score is not None]
    avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0

    return ConversationAnalytics(
        conversation_id=conversation_id,
        total_turns=total_turns,
        avg_latency=round(avg_latency, 3),
        rag_hit_rate=rag_hit_rate,
        repair_rate=repair_rate,
        avg_sentiment=avg_sentiment
    )


def get_global_analytics(db: Session) -> GlobalAnalytics:
    total_users = db.query(func.count(User.id)).scalar()
    total_conversations = db.query(func.count(Conversation.id)).scalar()
    total_messages = db.query(func.count(Message.id)).scalar()

    all_assistant = db.query(Message).filter(Message.role == "assistant").all()

    latencies = [m.response_latency for m in all_assistant if m.response_latency]
    avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0

    rag_hits = sum(1 for m in all_assistant if m.rag_hit)
    rag_hit_rate = round(rag_hits / max(len(all_assistant), 1), 2)

    all_msgs = db.query(Message).all()
    repairs = sum(1 for m in all_msgs if m.is_repair_turn)
    repair_rate = round(repairs / max(len(all_msgs), 1), 2)

    sentiments = [m.sentiment_score for m in all_msgs if m.sentiment_score is not None]
    avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0

    conversations = db.query(Conversation).all()
    avg_session = round(
        sum(c.total_turns for c in conversations) / max(len(conversations), 1), 2
    )

    return GlobalAnalytics(
        total_users=total_users,
        total_conversations=total_conversations,
        total_messages=total_messages,
        avg_latency=avg_latency,
        rag_hit_rate=rag_hit_rate,
        repair_rate=repair_rate,
        avg_sentiment=avg_sentiment,
        avg_session_length=avg_session
    )
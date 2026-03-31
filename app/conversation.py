from sqlalchemy.orm import Session
from app.models import Conversation, Message
from app.config import settings
from app.llm import summarize_conversation


def get_conversation_history(
    db: Session,
    conversation_id: str
) -> list[dict]:
    """
    Return recent messages as list of {role, content} dicts.
    If older turns exist beyond MAX_HISTORY_TURNS, they are summarized.
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    max_turns = settings.MAX_HISTORY_TURNS

    if len(messages) <= max_turns:
        return [{"role": m.role, "content": m.content} for m in messages]

    old_messages = messages[:-max_turns]
    recent_messages = messages[-max_turns:]

    old_turns = [{"role": m.role, "content": m.content} for m in old_messages]
    summary_text = summarize_conversation(old_turns)

    history = [{"role": "system", "content": f"[Earlier conversation summary]: {summary_text}"}]
    history += [{"role": m.role, "content": m.content} for m in recent_messages]
    return history


def detect_repair(user_message: str) -> bool:
    """Detect if the user is correcting or repairing the conversation."""
    repair_phrases = [
        "that's not what i meant", "you misunderstood", "no, i meant",
        "that's wrong", "not correct", "you're wrong", "actually,",
        "let me clarify", "i said", "that's not right", "incorrect"
    ]
    lower = user_message.lower()
    return any(phrase in lower for phrase in repair_phrases)


def compute_sentiment(text: str) -> float:
    """
    Simple keyword-based sentiment scoring.
    Returns a float from -1.0 (very negative) to 1.0 (very positive).
    """
    positive_words = ["thanks", "great", "perfect", "awesome", "helpful",
                      "good", "excellent", "solved", "works", "love", "amazing"]
    negative_words = ["frustrated", "useless", "broken", "terrible", "awful",
                      "hate", "doesn't work", "not working", "failed", "bad", "worse"]

    lower = text.lower()
    pos = sum(1 for w in positive_words if w in lower)
    neg = sum(1 for w in negative_words if w in lower)

    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def update_conversation_stats(db: Session, conversation_id: str, latency: float):
    """Recompute and persist avg latency and total turns on the conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        return

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.role == "assistant"
    ).all()

    latencies = [m.response_latency for m in messages if m.response_latency]
    conv.avg_response_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
    conv.total_turns = len(messages)
    db.commit()
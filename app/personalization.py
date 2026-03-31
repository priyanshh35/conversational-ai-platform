from sqlalchemy.orm import Session
from app.models import User


def build_system_prompt(user: User, rag_context: str = "") -> str:
    """
    Builds a personalized system prompt based on the user's profile.
    Injects tone, verbosity, expertise level, and RAG context.
    """
    profile = user.profile or {}
    tone = profile.get("tone", "neutral")
    verbosity = profile.get("verbosity", "medium")
    expertise = profile.get("expertise_level", "intermediate")
    topics = profile.get("topics_of_interest", [])

    # Tone instruction
    tone_instruction = {
        "formal": "Use a professional, formal tone. Avoid contractions and slang.",
        "casual": "Use a friendly, casual tone. Contractions and light humor are welcome.",
        "neutral": "Use a clear, neutral tone that is neither too formal nor too casual."
    }.get(tone, "Use a clear, neutral tone.")

    # Verbosity instruction
    verbosity_instruction = {
        "brief": "Keep responses concise — 2-3 sentences maximum unless more detail is explicitly needed.",
        "medium": "Provide moderate detail — enough to fully answer but without unnecessary padding.",
        "detailed": "Provide thorough, detailed responses with examples and step-by-step breakdowns."
    }.get(verbosity, "Provide moderate detail.")

    # Expertise instruction
    expertise_instruction = {
        "beginner": "Assume the user is a beginner. Avoid technical jargon and explain every concept simply.",
        "intermediate": "Assume the user has some technical knowledge. Balance simplicity and depth.",
        "expert": "Assume the user is an expert. Use technical terminology freely and skip basic explanations."
    }.get(expertise, "Assume moderate technical knowledge.")

    # Topics
    topics_str = f"The user is particularly interested in: {', '.join(topics)}." if topics else ""

    # RAG context block
    rag_block = ""
    if rag_context.strip():
        rag_block = f"""
--- RELEVANT KNOWLEDGE BASE CONTEXT ---
{rag_context}
--- END CONTEXT ---
Use the above context to inform your response if relevant. Do not fabricate information not present in the context.
"""

    system_prompt = f"""You are a helpful Tech Support AI assistant.

{tone_instruction}
{verbosity_instruction}
{expertise_instruction}
{topics_str}

{rag_block}

Always be honest when you don't know something. Offer to escalate to human support for complex unresolved issues."""

    return system_prompt.strip()


def update_profile(db: Session, user_id: str, updates: dict) -> dict:
    """Merge profile updates into the user's existing profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    current_profile = user.profile or {}
    updated_profile = {**current_profile, **updates}

    # Validate allowed values
    valid_tones = {"formal", "casual", "neutral"}
    valid_verbosity = {"brief", "medium", "detailed"}
    valid_expertise = {"beginner", "intermediate", "expert"}

    if updated_profile.get("tone") not in valid_tones:
        updated_profile["tone"] = "neutral"
    if updated_profile.get("verbosity") not in valid_verbosity:
        updated_profile["verbosity"] = "medium"
    if updated_profile.get("expertise_level") not in valid_expertise:
        updated_profile["expertise_level"] = "intermediate"

    user.profile = updated_profile
    db.commit()
    return updated_profile
"""
Run once to populate ChromaDB with Tech Support knowledge base.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.rag import add_documents, get_collection
from dotenv import load_dotenv
load_dotenv()

# Category 1: Tech Support FAQs
TECH_SUPPORT_DOCS = [
    {
        "id": "ts_001",
        "text": "To reset your password, go to the login page and click 'Forgot Password'. Enter your registered email. You will receive a reset link within 5 minutes. Check your spam folder if you don't see it.",
        "metadata": {"category": "account", "subcategory": "password", "difficulty": "easy"}
    },
    {
        "id": "ts_002",
        "text": "If the app is crashing on startup, try these steps: 1) Clear the app cache in Settings > Apps > Clear Cache. 2) Restart your device. 3) Uninstall and reinstall the app. 4) Check if your OS version is supported.",
        "metadata": {"category": "troubleshooting", "subcategory": "crash", "difficulty": "medium"}
    },
    {
        "id": "ts_003",
        "text": "Internet connectivity issues: First check if other websites load. If yes, try clearing browser cache with Ctrl+Shift+Delete. Disable VPN or proxy if active. Flush DNS by running 'ipconfig /flushdns' on Windows or 'sudo dscacheutil -flushcache' on Mac.",
        "metadata": {"category": "troubleshooting", "subcategory": "network", "difficulty": "medium"}
    },
    {
        "id": "ts_004",
        "text": "To enable two-factor authentication (2FA): Go to Account Settings > Security > Two-Factor Authentication. Choose between SMS or authenticator app (Google Authenticator recommended). Scan the QR code and enter the 6-digit code to confirm.",
        "metadata": {"category": "account", "subcategory": "security", "difficulty": "easy"}
    },
    {
        "id": "ts_005",
        "text": "Billing questions: Invoices are generated on the 1st of each month. You can download them from Billing > Invoice History. Accepted payment methods: Visa, Mastercard, PayPal. For refund requests, contact billing@company.com within 30 days of charge.",
        "metadata": {"category": "billing", "subcategory": "invoice", "difficulty": "easy"}
    },
    {
        "id": "ts_006",
        "text": "API rate limits: Free plan allows 100 requests/minute. Pro plan allows 1000 requests/minute. Enterprise is unlimited. If you exceed the limit, you'll receive a 429 Too Many Requests error. Implement exponential backoff in your client.",
        "metadata": {"category": "api", "subcategory": "rate_limits", "difficulty": "hard"}
    },
    {
        "id": "ts_007",
        "text": "Data export: You can export all your data in CSV or JSON format from Settings > Data > Export. Large exports are processed in the background and you'll receive an email with a download link when ready. Export links expire after 24 hours.",
        "metadata": {"category": "data", "subcategory": "export", "difficulty": "easy"}
    },
    {
        "id": "ts_008",
        "text": "Slow performance troubleshooting: Check your internet speed at speedtest.net (minimum 10 Mbps recommended). Close unused browser tabs. Disable browser extensions. Try an incognito window. If on mobile, enable WiFi instead of cellular data.",
        "metadata": {"category": "troubleshooting", "subcategory": "performance", "difficulty": "medium"}
    },
    {
        "id": "ts_009",
        "text": "Account deletion is permanent and cannot be undone. To delete your account: Settings > Account > Delete Account. You will receive a confirmation email. Click confirm within 48 hours. All data will be purged within 30 days per our privacy policy.",
        "metadata": {"category": "account", "subcategory": "deletion", "difficulty": "easy"}
    },
    {
        "id": "ts_010",
        "text": "Webhook setup: Go to Developer Settings > Webhooks > Add Endpoint. Enter your HTTPS endpoint URL. Select the events to subscribe to. Save and copy the signing secret. Verify webhooks by checking the X-Signature-256 header on incoming requests.",
        "metadata": {"category": "api", "subcategory": "webhooks", "difficulty": "hard"}
    },
]

# Category 2: Conversation Repair Patterns
REPAIR_PATTERNS = [
    {
        "id": "rep_001",
        "text": "When a user says 'that's not what I meant' or 'you misunderstood me', immediately acknowledge the confusion, briefly restate what you understood, and ask a focused clarifying question to get back on track.",
        "metadata": {"category": "repair", "trigger": "misunderstanding"}
    },
    {
        "id": "rep_002",
        "text": "When a user expresses frustration (e.g., 'this is useless', 'why isn't this working'), de-escalate by validating their frustration, summarizing the problem clearly, and offering a concrete next step or escalation path.",
        "metadata": {"category": "repair", "trigger": "frustration"}
    },
    {
        "id": "rep_003",
        "text": "When a user asks the same question twice, recognize this as a signal that the previous answer was insufficient. Acknowledge this, try a different explanation approach, and offer to escalate to human support if needed.",
        "metadata": {"category": "repair", "trigger": "repetition"}
    },
]

# Category 3: Conversation Style Templates
STYLE_TEMPLATES = [
    {
        "id": "style_001",
        "text": "For formal users: Use complete sentences, professional vocabulary, no contractions, cite sources when possible, and structure responses with clear sections.",
        "metadata": {"category": "style", "tone": "formal"}
    },
    {
        "id": "style_002",
        "text": "For casual users: Use a friendly conversational tone, contractions are fine, keep responses concise, use bullet points for lists, and add light encouragement.",
        "metadata": {"category": "style", "tone": "casual"}
    },
    {
        "id": "style_003",
        "text": "For expert users: Skip basic explanations, use technical terminology freely, provide command-line examples where relevant, and link to advanced documentation.",
        "metadata": {"category": "style", "expertise": "expert"}
    },
    {
        "id": "style_004",
        "text": "For beginner users: Use simple language, avoid jargon, explain every step, provide visual analogies, confirm understanding after each major step.",
        "metadata": {"category": "style", "expertise": "beginner"}
    },
]


def main():
    print("Seeding knowledge base...")

    collection = get_collection()
    existing_ids = set(collection.get()["ids"])

    all_docs = TECH_SUPPORT_DOCS + REPAIR_PATTERNS + STYLE_TEMPLATES

    new_docs = [d for d in all_docs if d["id"] not in existing_ids]

    if not new_docs:
        print(f"Knowledge base already seeded with {len(all_docs)} documents. Nothing to add.")
        return

    print(f"Adding {len(new_docs)} documents...")
    add_documents(new_docs)
    print(f"Done. Knowledge base now has {collection.count()} documents.")


if __name__ == "__main__":
    main()
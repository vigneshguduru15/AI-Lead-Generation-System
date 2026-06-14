import gradio as gr
from flask import Flask, request
import requests
import os
import threading

app = Flask(__name__)

# ─────────────────────────────────────────
# ENV VARIABLES
# ─────────────────────────────────────────
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# ─────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────
from lead_classifier import classify_lead
from auto_reply import generate_reply
from escalation import should_escalate
from crm import save_lead

# ─────────────────────────────────────────
# INSTAGRAM REPLY FUNCTION
# ─────────────────────────────────────────

def send_instagram_reply(recipient_id, message_text):
    """Send auto reply back to Instagram DM"""
    url = "https://graph.facebook.com/v23.0/me/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    params = {"access_token": PAGE_ACCESS_TOKEN}

    try:
        response = requests.post(url, json=payload, params=params, timeout=10)
        print(f"Instagram reply status: {response.status_code}")
        print(f"Instagram reply response: {response.text}")
        return response
    except Exception as e:
        print(f"Error sending Instagram reply: {e}")
        return None


# ─────────────────────────────────────────
# CORE LEAD PROCESSING FUNCTION
# ─────────────────────────────────────────

def process_and_reply(sender_id, user_message, platform="Instagram"):
    """Full pipeline: classify → reply → save → send"""

    print(f"Processing message from {sender_id}: {user_message}")

    # Step 1 — Classify lead
    lead_type = classify_lead(user_message)
    print(f"Lead type: {lead_type}")

    # Step 2 — Generate AI reply
    ai_reply = generate_reply(user_message, lead_type)
    print(f"AI reply: {ai_reply}")

    # Step 3 — Save to CRM
    save_lead(
        sender_id,
        platform,
        sender_id,
        user_message,
        lead_type,
        ai_reply
    )
    print("Saved to CRM")

    # Step 4 — Send reply back on Instagram
    send_instagram_reply(sender_id, ai_reply)
    print("Reply sent to Instagram!")

    return lead_type, ai_reply


# ─────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────

@app.route("/")
def home():
    return "AI Lead Generation System Running Successfully", 200


@app.route("/test", methods=["GET"])
def test():
    return "OK", 200


@app.route("/vignesh")
def vignesh():
    return "VIGNESH_ROUTE_WORKING"


# ── Webhook Verification ──
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"Webhook verify — mode: {mode}, token: {token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED SUCCESSFULLY")
        return challenge, 200

    print("VERIFICATION FAILED")
    return "Verification failed", 403


# ── Receive Instagram Messages ──
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("WEBHOOK POST HIT")
    print("=" * 50)
    print(data)
    print("=" * 50)

    try:
        for entry in data.get("entry", []):

            # ── FORMAT 1: Instagram DMs via messaging[] ────────
            # This is the standard format for Instagram DMs
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                msg = event.get("message", {})
                user_message = msg.get("text", "")

                # Skip echo messages (messages sent by the page itself)
                if msg.get("is_echo"):
                    print("Skipping echo message")
                    continue

                if sender_id and user_message:
                    print(f"FORMAT 1 (messaging) — Sender: {sender_id}")
                    process_and_reply(sender_id, user_message, "Instagram")

            # ── FORMAT 2: Instagram events via changes[] ───────
            # This handles comments, mentions, and some DM formats
            for change in entry.get("changes", []):
                field = change.get("field", "")
                value = change.get("value", {})

                # Handle DMs in changes format
                if field == "messages":
                    sender_id = value.get("sender", {}).get("id")
                    user_message = value.get("message", {}).get("text", "")

                    if sender_id and user_message:
                        print(f"FORMAT 2 (changes/messages) — Sender: {sender_id}")
                        process_and_reply(sender_id, user_message, "Instagram")

                # Handle comments — Comment to DM automation
                elif field == "comments":
                    commenter_id = value.get("from", {}).get("id")
                    comment_text = value.get("text", "").lower()

                    trigger_words = [
                        "interested", "price", "pricing",
                        "demo", "cost", "how much", "buy",
                        "want", "info", "details"
                    ]

                    if commenter_id and any(w in comment_text for w in trigger_words):
                        print(f"Comment trigger detected from {commenter_id}: {comment_text}")
                        dm_message = (
                            f"Hi! Thanks for your interest in Tilesview. "
                            f"I saw your comment and would love to help you! "
                            f"What would you like to know more about?"
                        )
                        process_and_reply(commenter_id, value.get("text", ""), "Instagram")

    except Exception as e:
        print(f"ERROR in webhook: {e}")
        import traceback
        traceback.print_exc()

    # Always return 200 to Meta — otherwise Meta will retry endlessly
    return "EVENT_RECEIVED", 200


# ─────────────────────────────────────────
# GRADIO MANUAL TESTING UI
# ─────────────────────────────────────────

def process_lead(name, platform, contact, message):
    if not message.strip():
        return "Please enter a customer message", "", ""

    lead_type = classify_lead(message)
    ai_reply = generate_reply(message, lead_type)
    save_lead(name, platform, contact, message, lead_type, ai_reply)

    escalation_status = (
        "YES - Escalated to Sales Team 🚨"
        if should_escalate(message)
        else "NO - AI Handled Conversation ✅"
    )

    result = f"""Lead Classification: {lead_type}

Name: {name}
Platform: {platform}
Contact: {contact}
Message: {message}"""

    return result, ai_reply, escalation_status


with gr.Blocks(title="AI Lead Qualification System") as demo:

    gr.Markdown("""
# AI Lead Qualification & Auto Reply System
### Tilesview / Tileswale Interview Assignment

Features:
- ✅ AI Lead Qualification (HOT / WARM / COLD)
- ✅ AI Auto Reply
- ✅ CRM Storage
- ✅ Human Escalation
- ✅ Instagram Webhook Integration
- ✅ Comment to DM Automation
""")

    with gr.Row():
        name = gr.Textbox(label="Customer Name", placeholder="John Doe")
        platform = gr.Dropdown(
            ["Instagram", "Facebook", "LinkedIn", "Website Chat"],
            label="Platform",
            value="Instagram"
        )

    contact = gr.Textbox(
        label="Contact Details",
        placeholder="Phone number or email"
    )

    message = gr.Textbox(
        lines=5,
        label="Customer Message",
        placeholder="Type the customer message here..."
    )

    gr.Examples(
        examples=[
            ["John", "Instagram", "+91 9999999999", "Can I get pricing for your tile visualization software?"],
            ["Sara", "Facebook", "sara@email.com", "I would like a demo of your product."],
            ["Mike", "LinkedIn", "+91 8888888888", "Can you tell me more about features?"],
            ["Raj",  "Instagram", "raj@email.com",  "Nice post!"],
            ["Priya", "Website Chat", "priya@email.com", "Please arrange a sales call."],
        ],
        inputs=[name, platform, contact, message]
    )

    submit = gr.Button("Analyze Lead", variant="primary")

    with gr.Row():
        lead_output = gr.Textbox(label="Lead Information", lines=6)
        reply_output = gr.Textbox(label="AI Generated Reply", lines=6)

    escalation_output = gr.Textbox(label="Escalation Status")

    submit.click(
        fn=process_lead,
        inputs=[name, platform, contact, message],
        outputs=[lead_output, reply_output, escalation_output]
    )


# ─────────────────────────────────────────
# RUN FLASK + GRADIO TOGETHER
# ─────────────────────────────────────────

def run_flask():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask started on port", os.environ.get("PORT", 10000))

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
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
# IMPORTS FROM YOUR OTHER FILES
# ─────────────────────────────────────────
from lead_classifier import classify_lead
from auto_reply import generate_reply
from escalation import should_escalate
from crm import save_lead

# ─────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────

@app.route("/")
def home():
    return "Instagram Webhook Running Successfully", 200


@app.route("/test", methods=["GET"])
def test():
    return "OK", 200

@app.route("/test-webhook", methods=["POST"])
def test_webhook():
    data = request.get_json()
    print("TEST WEBHOOK DATA:")
    print(data)
    return "OK", 200


@app.route("/vignesh")
def vignesh():
    return "VIGNESH_ROUTE_WORKING"

# ── Webhook Verification (Meta calls this first) ──
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("Mode:", mode)
    print("Token from Meta:", token)
    print("Expected Token:", VERIFY_TOKEN)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED SUCCESSFULLY")
        return challenge, 200

    print("VERIFICATION FAILED")
    return "Verification failed", 403


# ── Receive Instagram DMs ──
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("WEBHOOK POST HIT")
    print("=" * 50)
    print(data)
    print("=" * 50)

    try:
        for entry in data.get("entry", []):

            # Instagram sends via changes[], not messaging[]
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                sender_id = value.get("sender", {}).get("id")
                message_obj = value.get("message", {})
                user_message = message_obj.get("text", "")

                print(f"Sender: {sender_id}")
                print(f"Message: {user_message}")

                if not user_message or not sender_id:
                    print("No message or sender, skipping")
                    continue

                lead_type = classify_lead(user_message)
                print(f"Lead type: {lead_type}")

                ai_reply = generate_reply(user_message, lead_type)
                print(f"AI reply: {ai_reply}")

                save_lead(
                    sender_id, "Instagram",
                    sender_id, user_message,
                    lead_type, ai_reply
                )

                send_instagram_reply(sender_id, ai_reply)
                print("Reply sent successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    return "EVENT_RECEIVED", 200
# ─────────────────────────────────────────
# INSTAGRAM REPLY FUNCTION
# ─────────────────────────────────────────

def send_instagram_reply(recipient_id, message_text):
    url = f"https://graph.facebook.com/v23.0/me/messages"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    params = {"access_token": PAGE_ACCESS_TOKEN}
    
    response = requests.post(url, json=payload, params=params)
    
    print(f"Instagram reply status: {response.status_code}")
    print(f"Instagram reply response: {response.text}")
    
    return response


# ─────────────────────────────────────────
# GRADIO MANUAL TESTING UI
# ─────────────────────────────────────────

def process_lead(name, platform, contact, message):
    if not message.strip():
        return "Please enter a customer message", "", ""

    # Classify lead
    lead_type = classify_lead(message)

    # Generate reply
    ai_reply = generate_reply(message, lead_type)

    # Save to CRM
    save_lead(name, platform, contact, message, lead_type, ai_reply)

    # Check escalation
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
            ["Priya","Website Chat","priya@email.com","Please arrange a sales call."],
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
# RUN BOTH FLASK + GRADIO TOGETHER
# ─────────────────────────────────────────

def run_flask():
    """Run Flask in a separate thread"""
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False,   # Must be False when using threads
        use_reloader=False
    )


if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask started on port", os.environ.get("PORT", 10000))

    # Launch Gradio on port 7860
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
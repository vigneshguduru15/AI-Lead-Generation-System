import gradio as gr
from flask import Flask, request
import requests
import os

app = Flask(__name__)
@app.route("/")
def home():
    return "Instagram Webhook Running Successfully", 200

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
from lead_classifier import classify_lead
from auto_reply import generate_reply
from escalation import should_escalate
from crm import save_lead

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("Mode:", mode)
    print("Token from Meta:", token)
    print("Token from Render:", VERIFY_TOKEN)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403

@app.route("/test", methods=["GET"])
def test():
    print("TEST ROUTE HIT")
    return "OK", 200

@app.route("/vignesh")
def vignesh():
    return "VIGNESH_ROUTE_WORKING"

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()
    
    print("WEBHOOK HIT")
    print("="*50)
    print(data)
    print("="*50)
    

    try:
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                sender_id = messaging_event["sender"]["id"]

                if "message" in messaging_event and "text" in messaging_event["message"]:

                    user_message = messaging_event["message"]["text"]

                    lead_type = classify_lead(user_message)

                    ai_reply = generate_reply(
                        user_message,
                        lead_type
                    )

                    url = f"https://graph.facebook.com/v23.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

                    payload = {
                        "recipient": {
                            "id": sender_id
                        },
                        "message": {
                            "text": ai_reply
                        }
                    }

                    response = requests.post(
                        url,
                        json=payload
                    )

                    print(response.text)

    except Exception as e:
        print("ERROR:", e)

    return "EVENT_RECEIVED", 200


def process_lead(
    name,
    platform,
    contact,
    message
):

    if not message.strip():

        return (
            "Please enter a customer message",
            "",
            ""
        )

    lead_type = classify_lead(message)

    ai_reply = generate_reply(
        message,
        lead_type
    )

    save_lead(
        name,
        platform,
        contact,
        message,
        lead_type,
        ai_reply
    )

    escalation_status = (
        "YES - Escalated to Sales Team 🚨"
        if should_escalate(message)
        else "NO - AI Handled Conversation ✅"
    )

    result = f"""
Lead Type: {lead_type}

Name: {name}

Platform: {platform}

Contact: {contact}
"""

    return (
        result,
        ai_reply,
        escalation_status
    )


with gr.Blocks() as demo:

    gr.Markdown("""
# AI Lead Qualification & Auto Reply System

### Tilesview / Tileswale Interview Assignment

Features:
- AI Lead Qualification
- AI Auto Reply
- CRM Storage
- Human Escalation
""")

    name = gr.Textbox(
        label="Customer Name"
    )

    platform = gr.Dropdown(
        [
            "Instagram",
            "Facebook",
            "LinkedIn",
            "Website Chat"
        ],
        label="Platform"
    )

    contact = gr.Textbox(
        label="Contact Details"
    )

    message = gr.Textbox(
        lines=5,
        label="Customer Message"
    )

    submit = gr.Button(
        "Analyze Lead"
    )

    lead_output = gr.Textbox(
        label="Lead Information"
    )

    reply_output = gr.Textbox(
        label="AI Generated Reply",
        lines=6
    )

    escalation_output = gr.Textbox(
        label="Escalation Status"
    )

    submit.click(
        fn=process_lead,
        inputs=[
            name,
            platform,
            contact,
            message
        ],
        outputs=[
            lead_output,
            reply_output,
            escalation_output
        ]
    )

#demo.launch(share=True)
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
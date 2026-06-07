import gradio as gr
from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("vignesh123")
PAGE_ACCESS_TOKEN = os.getenv("EABAozbMW2UsBRi52OLZAgSPQr7bjZA89DnRBukjBKfXzgdc9z2NdbLr7hVZBSa03SOwLdRBXZBJ3nebo3ZBHXZChkBFnKLVxWFFmHSptM7nhbWkZCNkaR9yP4f8csVnE2PLZBxtBjp7pKLWDttYU9QCiemFPM4ojbSGk7VZCErbUvpE9zlKH3tLqIn0ML7QNL3E5BahETZBoeN7X3JkZCB2vuVusA9603Q5LaEwN9ImPCU0Sz3A")
from lead_classifier import classify_lead
from auto_reply import generate_reply
from escalation import should_escalate
from crm import save_lead

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403

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

demo.launch(share=True)
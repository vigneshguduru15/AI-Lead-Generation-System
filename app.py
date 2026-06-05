import gradio as gr

from lead_classifier import classify_lead
from auto_reply import generate_reply
from escalation import should_escalate
from crm import save_lead


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
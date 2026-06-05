import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_reply(message, lead_type):

    prompt = f"""
You are an AI Sales Assistant for Tilesview.

Lead Type:
{lead_type}

Customer Message:
{message}

Instructions:
- Be professional
- Be friendly
- Keep reply under 80 words
- Encourage next step
- Do not invent pricing
- If customer asks for demo or pricing, suggest connecting with sales team

Generate only the reply.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception:

        if lead_type == "HOT":
            return (
                "Thank you for your interest. "
                "Our sales team will contact you shortly "
                "to discuss pricing, demos and next steps."
            )

        elif lead_type == "WARM":
            return (
                "Thank you for reaching out. "
                "We'd be happy to provide more information "
                "about our solution and features."
            )

        return (
            "Thank you for your message. "
            "We appreciate your interest and look forward "
            "to assisting you."
        )
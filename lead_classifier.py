import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-1.5-flash")


def classify_lead(message):

    prompt = f"""
You are a lead qualification expert.

Classify this customer message as:

HOT
WARM
COLD

Rules:

HOT:
- Wants pricing
- Wants demo
- Wants sales call
- Ready to buy

WARM:
- Interested
- Asking features
- Wants information

COLD:
- Casual comment
- Not interested
- General conversation

Return ONLY one word:
HOT or WARM or COLD

Message:
{message}
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip().upper()

    except Exception:

        msg = message.lower()

        if any(word in msg for word in [
            "price", "pricing", "demo",
            "call", "buy", "purchase", "sales"
        ]):
            return "HOT"

        elif any(word in msg for word in [
            "feature", "features",
            "details", "information",
            "interested"
        ]):
            return "WARM"

        return "COLD"
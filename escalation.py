def should_escalate(message):

    escalation_keywords = [
        "pricing",
        "price",
        "demo",
        "sales call",
        "call me",
        "buy",
        "purchase",
        "quotation",
        "quote"
    ]

    msg = message.lower()

    return any(
        keyword in msg
        for keyword in escalation_keywords
    )
import sqlite3

conn = sqlite3.connect(
    "leads.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    platform TEXT,
    contact TEXT,
    message TEXT,
    lead_type TEXT,
    ai_reply TEXT
)
""")

conn.commit()


def save_lead(
    name,
    platform,
    contact,
    message,
    lead_type,
    ai_reply
):

    cursor.execute(
        """
        INSERT INTO leads(
            name,
            platform,
            contact,
            message,
            lead_type,
            ai_reply
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            platform,
            contact,
            message,
            lead_type,
            ai_reply
        )
    )

    conn.commit()
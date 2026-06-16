import sqlite3
from pathlib import Path

DB_PATH = Path("tickets.db")

conn   = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Main tickets table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id     TEXT PRIMARY KEY,
        issue         TEXT NOT NULL,
        category      TEXT NOT NULL DEFAULT 'IT',
        status        TEXT NOT NULL DEFAULT 'Open',
        priority      TEXT NOT NULL DEFAULT 'Low',
        employee_name TEXT,
        employee_id   TEXT,
        department    TEXT,
        session_id    TEXT,
        created_at    TEXT NOT NULL,
        updated_at    TEXT NOT NULL
    )
""")

# Pending ticket flow table (survives server restarts)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_tickets (
        session_id  TEXT PRIMARY KEY,
        issue       TEXT NOT NULL,
        category    TEXT NOT NULL DEFAULT 'IT',
        stage       TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    )
""")

conn.commit()
conn.close()

print("Database schema verified/created successfully.")
print(f"Location: {DB_PATH.resolve()}")

# Show current ticket count
conn2  = sqlite3.connect(DB_PATH)
cursor2 = conn2.cursor()
cursor2.execute("SELECT COUNT(*) FROM tickets")
count = cursor2.fetchone()[0]
print(f"Current tickets in DB: {count}")
conn2.close()
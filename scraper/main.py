import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
from .utils import parse_comments, detection_misattribution

BASE_URL = "https://portal.crt.gob.mx/ConsultaPublica/Detalle/"
CONSULTATION_ID = 19
MISATTRIBUTED_ID = 15


def fetch_comments():
    url = f"{BASE_URL}{CONSULTATION_ID}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    comments = parse_comments(soup)
    # Mark mis‑attributed ones
    for c in comments:
        c["is_misattributed"] = detection_misattribution(c["text"]) 
    return comments


def store_comments(comments):
    conn = sqlite3.connect("data/comments.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            consultation_id INTEGER,
            text TEXT,
            author TEXT,
            timestamp TEXT,
            source_url TEXT,
            is_misattributed INTEGER
        )
    """)
    for c in comments:
        cur.execute(
            "INSERT OR REPLACE INTO comments (id, consultation_id, text, author, timestamp, source_url, is_misattributed) VALUES (?,?,?,?,?,?,?)",
            (
                c["id"],
                CONSULTATION_ID,
                c["text"],
                c.get("author", ""),
                c.get("timestamp", datetime.utcnow().isoformat()),
                c.get("source_url", ""),
                int(c["is_misattributed"]),
            ),
        )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    comments = fetch_comments()
    store_comments(comments)
    print(f"Stored {len(comments)} comments")

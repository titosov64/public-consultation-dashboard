import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

import sys
from pathlib import Path
# Ensure the repository root is on the Python path so imports work on Streamlit Cloud
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

# Import scraper functions
from scraper.main import fetch_comments, store_comments
from streamlit_autorefresh import st_autorefresh

# Path to SQLite DB (will be created in the repo; Streamlit Cloud provides read/write space)
DB_PATH = Path("data/comments.db")

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# ---------- Helper utilities ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            consultation_id INTEGER,
            text TEXT,
            author TEXT,
            timestamp TEXT,
            source_url TEXT,
            is_misattributed INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

def load_comments(misattributed: bool | None = None) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if misattributed is None:
            cur.execute("SELECT * FROM comments")
        else:
            cur.execute(
                "SELECT * FROM comments WHERE is_misattributed = ?",
                (int(misattributed),),
            )
        rows = cur.fetchall()
    df = pd.DataFrame([dict(row) for row in rows])
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

def refresh_data():
    # Run scraper and store results – wrapped in a cached function to avoid duplicate runs in the same session.
    comments = fetch_comments()
    store_comments(comments)
    st.success(f"Fetched and stored {len(comments)} comments (run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Public Consultation 19 Dashboard", layout="wide")
st.title("Public Consultation 19 – Executive Dashboard")

# Initialize DB on first run
init_db()

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    if st.button("Refresh data (scrape portal)"):
        refresh_data()
    refresh_interval = st.selectbox(
        "Auto‑refresh interval",
        options=["Never", "5 min", "15 min", "30 min", "1 hour"],
        index=0,
    )
    st.caption("Auto‑refresh works only while the app session is active.")

if refresh_interval != "Never":
    minutes = {"5 min": 5, "15 min": 15, "30 min": 30, "1 hour": 60}[refresh_interval]
    st_autorefresh(interval=minutes * 60 * 1000, key=f"autorefresh-{minutes}")

# Load data
all_df = load_comments()
mis_df = load_comments(misattributed=True)

# Stats
col1, col2 = st.columns(2)
col1.metric("Total comments", len(all_df))
col2.metric("Mis‑attributed (to 15)", len(mis_df))

st.markdown("---")

# Recent comments (all)
st.subheader("Latest Comments (All)")
if not all_df.empty:
    recent_all = all_df.sort_values("timestamp", ascending=False).head(20)
    def highlight_mis(row):
        return ["background-color: #ffdddd" if row["is_misattributed"] else "" for _ in row]
    st.dataframe(recent_all.style.apply(highlight_mis, axis=1))
else:
    st.info("No comments available yet.")

st.subheader("Mis‑attributed Comments (Consultation 15)")
if not mis_df.empty:
    recent_mis = mis_df.sort_values("timestamp", ascending=False).head(20)
    st.dataframe(recent_mis)
else:
    st.info("No mis‑attributed comments detected.")

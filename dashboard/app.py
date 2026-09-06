import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Public Consultation Dashboard", layout="wide")

st.title("Public Consultation 19 – Executive Dashboard")

# Fetch stats
try:
    stats_resp = requests.get(f"{API_URL}/stats")
    stats_resp.raise_for_status()
    stats = stats_resp.json()
except Exception as e:
    st.error(f"Failed to load stats: {e}")
    st.stop()

col1, col2 = st.columns(2)
col1.metric("Total Comments", stats["total_comments"])
col2.metric("Mis‑attributed (to 15)", stats["misattributed_comments"])

st.markdown("---")

# Show recent comments
st.subheader("Latest Comments (All)")
try:
    comments_resp = requests.get(f"{API_URL}/comments")
    comments_resp.raise_for_status()
    all_comments = comments_resp.json()["comments"]
except Exception as e:
    st.error(f"Failed to load comments: {e}")
    all_comments = []

# Show as table, highlight misattributed
if all_comments:
    # Convert to DataFrame for nicer display
    import pandas as pd
    df = pd.DataFrame(all_comments)
    # Ensure timestamp is parsed nicely
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Sort by newest first
    df = df.sort_values(by="timestamp", ascending=False).head(20)
    # Highlight misattributed rows
    def highlight_mis(row):
        return ["background-color: #ffdddd" if row["is_misattributed"] else "" for _ in row]
    st.dataframe(df.style.apply(highlight_mis, axis=1))
else:
    st.info("No comments available yet.")

st.subheader("Mis‑attributed Comments (Consultation 15)")
try:
    mis_resp = requests.get(f"{API_URL}/misattributed")
    mis_resp.raise_for_status()
    mis_comments = mis_resp.json()["comments"]
except Exception as e:
    st.error(f"Failed to load mis‑attributed comments: {e}")
    mis_comments = []

if mis_comments:
    df_mis = pd.DataFrame(mis_comments)
    if "timestamp" in df_mis.columns:
        df_mis["timestamp"] = pd.to_datetime(df_mis["timestamp"], errors="coerce")
    df_mis = df_mis.sort_values(by="timestamp", ascending=False).head(20)
    st.dataframe(df_mis)
else:
    st.info("No mis‑attributed comments detected.")

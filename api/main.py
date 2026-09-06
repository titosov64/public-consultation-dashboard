import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from .models import Comment, Stats, CommentsResponse
from .deps import get_db

# Import scraper functions
from scraper.main import fetch_comments, store_comments

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

app = FastAPI(title="Public Consultation Dashboard API")

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scheduler instance (will be started on startup)
scheduler = BackgroundScheduler()

def run_scrape_job():
    try:
        logger.info("Running scheduled scrape job...")
        comments = fetch_comments()
        store_comments(comments)
        logger.info(f"Scrape job stored {len(comments)} comments")
    except Exception as e:
        logger.exception(f"Error during scheduled scrape: {e}")

@app.on_event("startup")
async def startup_event():
    # Run initial scrape synchronously
    run_scrape_job()
    # Schedule periodic scraping every 5 minutes
    scheduler.add_job(run_scrape_job, trigger=IntervalTrigger(minutes=5), id="scrape_job", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started for periodic scraping")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

# Helper to query DB
def query_comments(db, misattributed: bool = None):
    cur = db.cursor()
    if misattributed is None:
        cur.execute("SELECT id, consultation_id, text, author, timestamp, source_url, is_misattributed FROM comments")
    else:
        cur.execute(
            "SELECT id, consultation_id, text, author, timestamp, source_url, is_misattributed FROM comments WHERE is_misattributed = ?",
            (int(misattributed),),
        )
    rows = cur.fetchall()
    comments = []
    for row in rows:
        comments.append(
            Comment(
                id=row[0],
                consultation_id=row[1],
                text=row[2],
                author=row[3],
                timestamp=row[4],
                source_url=row[5],
                is_misattributed=bool(row[6]),
            )
        )
    return comments

@app.get("/stats", response_model=Stats)
def get_stats(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM comments")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM comments WHERE is_misattributed = 1")
    mis = cur.fetchone()[0]
    # Assuming all stored comments belong to consultation 19
    return Stats(total_comments=total, misattributed_comments=mis, consultation_id=19)

@app.get("/comments", response_model=CommentsResponse)
def get_all_comments(db: sqlite3.Connection = Depends(get_db)):
    comments = query_comments(db)
    return CommentsResponse(comments=comments)

@app.get("/misattributed", response_model=CommentsResponse)
def get_misattributed_comments(db: sqlite3.Connection = Depends(get_db)):
    comments = query_comments(db, misattributed=True)
    return CommentsResponse(comments=comments)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import sqlite3
from typing import Generator

DATABASE = "data/comments.db"


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()

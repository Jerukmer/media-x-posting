#!/usr/bin/env python3
"""
state.py — SQLite state: dedupe posted links, track queue, log activity.
Simple, single file DB at state.db next to this script.
"""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS posted (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT UNIQUE,
        title TEXT,
        tweet_text TEXT,
        content_type TEXT,
        posted_at INTEGER
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS seen (
        link TEXT PRIMARY KEY,
        seen_at INTEGER
    )""")
    return conn

def is_seen(link):
    with _conn() as c:
        row = c.execute("SELECT 1 FROM seen WHERE link=?", (link,)).fetchone()
        return row is not None

def mark_seen(link):
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO seen (link, seen_at) VALUES (?,?)", (link, int(time.time())))

def is_posted(link):
    with _conn() as c:
        row = c.execute("SELECT 1 FROM posted WHERE link=?", (link,)).fetchone()
        return row is not None

def mark_posted(link, title, tweet_text, content_type):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO posted (link, title, tweet_text, content_type, posted_at) VALUES (?,?,?,?,?)",
            (link, title, tweet_text, content_type, int(time.time()))
        )
        c.execute("INSERT OR IGNORE INTO seen (link, seen_at) VALUES (?,?)", (link, int(time.time())))

def stats():
    with _conn() as c:
        posted = c.execute("SELECT COUNT(*) FROM posted").fetchone()[0]
        seen = c.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
    return {"posted": posted, "seen": seen}

def recent_posts(n=10):
    with _conn() as c:
        rows = c.execute(
            "SELECT link, title, tweet_text, content_type, posted_at FROM posted ORDER BY posted_at DESC LIMIT ?",
            (n,)
        ).fetchall()
    return [
        {"link": r[0], "title": r[1], "tweet_text": r[2], "content_type": r[3], "posted_at": r[4]}
        for r in rows
    ]

if __name__ == "__main__":
    print(stats())

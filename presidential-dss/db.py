"""
db.py — PDSS Persistent Storage Layer
SQLite-backed database for briefs, distributions, and messaging.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "pdss.db")

# ── User directory with roles ────────────────────────────────────────────────
USERS = {
    "president": {
        "password": "eagle1600",
        "role":     "president",
        "title":    "President of the United States",
        "display":  "POTUS",
    },
    "vp": {
        "password": "vp2025",
        "role":     "chain",
        "title":    "Vice President",
        "display":  "VPOTUS",
    },
    "secdef": {
        "password": "pentagon2025",
        "role":     "chain",
        "title":    "Secretary of Defense",
        "display":  "SECDEF",
    },
    "secstate": {
        "password": "foggy2025",
        "role":     "chain",
        "title":    "Secretary of State",
        "display":  "SECSTATE",
    },
    "nsa": {
        "password": "nsc2025",
        "role":     "chain",
        "title":    "National Security Advisor",
        "display":  "NSA",
    },
    "cia": {
        "password": "langley2025",
        "role":     "chain",
        "title":    "Director of Central Intelligence",
        "display":  "DCI",
    },
    "cjcs": {
        "password": "joint2025",
        "role":     "chain",
        "title":    "Chairman, Joint Chiefs of Staff",
        "display":  "CJCS",
    },
    "cos": {
        "password": "chiefs2025",
        "role":     "chain",
        "title":    "White House Chief of Staff",
        "display":  "COS",
    },
    "advisor": {
        "password": "sitroom2025",
        "role":     "chain",
        "title":    "Senior Policy Advisor",
        "display":  "ADVISOR",
    },
    "admin": {
        "password": "admin",
        "role":     "admin",
        "title":    "System Administrator",
        "display":  "ADMIN",
    },
}

# ── Schema ───────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS briefs (
    id          TEXT PRIMARY KEY,
    operator    TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    scenario    TEXT NOT NULL,
    severity    TEXT NOT NULL,
    verdict     TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS distributions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    briefing_id  TEXT NOT NULL,
    from_user    TEXT NOT NULL,
    to_user      TEXT NOT NULL,
    note         TEXT DEFAULT '',
    sent_at      TEXT NOT NULL,
    read_at      TEXT DEFAULT NULL,
    FOREIGN KEY (briefing_id) REFERENCES briefs(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user   TEXT NOT NULL,
    to_user     TEXT NOT NULL,
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    briefing_id TEXT DEFAULT NULL,
    sent_at     TEXT NOT NULL,
    read_at     TEXT DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_dist_to   ON distributions(to_user);
CREATE INDEX IF NOT EXISTS idx_dist_bid  ON distributions(briefing_id);
CREATE INDEX IF NOT EXISTS idx_msg_to    ON messages(to_user);
CREATE INDEX IF NOT EXISTS idx_msg_from  ON messages(from_user);
"""

# ── Connection ────────────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

# ── Auth ──────────────────────────────────────────────────────────────────────
def authenticate(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if user and user["password"] == password:
        return {"username": username, **user}
    return None

def get_user(username: str) -> dict | None:
    u = USERS.get(username)
    if u:
        return {"username": username, **u}
    return None

def get_all_users() -> list[dict]:
    return [{"username": k, **v} for k, v in USERS.items()]

def get_chain_users() -> list[dict]:
    """All users except president and admin — valid distribution targets."""
    return [{"username": k, **v} for k, v in USERS.items()
            if v["role"] in ("chain",)]

# ── Briefs ────────────────────────────────────────────────────────────────────
def save_brief(result: dict):
    """Persist a full result dict to the database."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO briefs (id, operator, timestamp, scenario, severity, verdict, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                result["briefing_id"],
                result["operator"],
                result["timestamp"],
                result["scenario_raw"][:500],
                result["severity"],
                result["verdict"],
                json.dumps(result, default=str),
                datetime.now(timezone.utc).isoformat(),
            )
        )

def load_brief(briefing_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT result_json FROM briefs WHERE id = ?", (briefing_id,)).fetchone()
    if row:
        return json.loads(row["result_json"])
    return None

def list_briefs(operator: str = None, limit: int = 50) -> list[dict]:
    """List brief summaries, optionally filtered by operator."""
    with get_conn() as conn:
        if operator:
            rows = conn.execute(
                "SELECT id, operator, timestamp, scenario, severity, verdict FROM briefs "
                "WHERE operator = ? ORDER BY created_at DESC LIMIT ?",
                (operator, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, operator, timestamp, scenario, severity, verdict FROM briefs "
                "ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]

def list_distributed_briefs(username: str) -> list[dict]:
    """Briefs distributed to a specific user."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT b.id, b.operator, b.timestamp, b.scenario, b.severity, b.verdict,
                      d.note, d.sent_at, d.read_at, d.id as dist_id
               FROM distributions d
               JOIN briefs b ON d.briefing_id = b.id
               WHERE d.to_user = ?
               ORDER BY d.sent_at DESC""",
            (username,)
        ).fetchall()
    return [dict(r) for r in rows]

# ── Distributions ─────────────────────────────────────────────────────────────
def distribute_brief(briefing_id: str, from_user: str, to_users: list[str], note: str = ""):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        for to_user in to_users:
            # Avoid duplicate distributions
            existing = conn.execute(
                "SELECT id FROM distributions WHERE briefing_id = ? AND to_user = ?",
                (briefing_id, to_user)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO distributions (briefing_id, from_user, to_user, note, sent_at) VALUES (?, ?, ?, ?, ?)",
                    (briefing_id, from_user, to_user, note, now)
                )

def mark_brief_read(dist_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE distributions SET read_at = ? WHERE id = ? AND read_at IS NULL",
            (datetime.now(timezone.utc).isoformat(), dist_id)
        )

def get_unread_brief_count(username: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM distributions WHERE to_user = ? AND read_at IS NULL",
            (username,)
        ).fetchone()
    return row["cnt"] if row else 0

def get_distribution_list(briefing_id: str) -> list[dict]:
    """Who has a brief been sent to."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT to_user, sent_at, read_at FROM distributions WHERE briefing_id = ?",
            (briefing_id,)
        ).fetchall()
    return [dict(r) for r in rows]

# ── Messages ──────────────────────────────────────────────────────────────────
def send_message(from_user: str, to_user: str, subject: str, body: str, briefing_id: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (from_user, to_user, subject, body, briefing_id, sent_at) VALUES (?, ?, ?, ?, ?, ?)",
            (from_user, to_user, subject, body, briefing_id, datetime.now(timezone.utc).isoformat())
        )

def get_inbox(username: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE to_user = ? ORDER BY sent_at DESC",
            (username,)
        ).fetchall()
    return [dict(r) for r in rows]

def get_sent(username: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE from_user = ? ORDER BY sent_at DESC",
            (username,)
        ).fetchall()
    return [dict(r) for r in rows]

def mark_message_read(msg_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE messages SET read_at = ? WHERE id = ? AND read_at IS NULL",
            (datetime.now(timezone.utc).isoformat(), msg_id)
        )

def get_unread_message_count(username: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE to_user = ? AND read_at IS NULL",
            (username,)
        ).fetchone()
    return row["cnt"] if row else 0

def get_conversation(user_a: str, user_b: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE (from_user=? AND to_user=?) OR (from_user=? AND to_user=?) ORDER BY sent_at ASC",
            (user_a, user_b, user_b, user_a)
        ).fetchall()
    return [dict(r) for r in rows]

def delete_brief(briefing_id: str):
    """Delete a brief and its associated distributions."""
    with get_conn() as conn:
        conn.execute("DELETE FROM distributions WHERE briefing_id = ?", (briefing_id,))
        conn.execute("DELETE FROM briefs WHERE id = ?", (briefing_id,))

def delete_message(msg_id: int):
    """Delete a single message."""
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE id = ?", (msg_id,))

# ── Init on import ────────────────────────────────────────────────────────────
init_db()
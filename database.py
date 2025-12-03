import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join("data", "tasks.db")
os.makedirs("data", exist_ok=True)

def _get_conn():
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """ 
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        text TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """
    )
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        task_id INTEGER,
        remind_at TEXT NOT NULL,
        sent INTEGER NOT NULL DEFAULT 0,
        repeat TEXT DEFAULT NULL
    )
    """
    )
    conn.commit()
    # basic migration: ensure expected columns exist
    cur.execute("PRAGMA table_info(reminders)")
    cols = [r[1] for r in cur.fetchall()]
    # if old 'send' column exists but 'sent' doesn't, add 'sent' and copy
    if "sent" not in cols:
        try:
            cur.execute("ALTER TABLE reminders ADD COLUMN sent INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except Exception:
            pass
    # ensure 'repeat' column exists
    cur.execute("PRAGMA table_info(reminders)")
    cols = [r[1] for r in cur.fetchall()]
    if "repeat" not in cols:
        try:
            cur.execute("ALTER TABLE reminders ADD COLUMN repeat TEXT DEFAULT NULL")
            conn.commit()
        except Exception:
            pass
    conn.close()

def add_task(user_id: str, text: str, created_at: str) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, text, done, created_at) VALUES (?, ?, 0, ?)",
                (user_id, text, created_at))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id

def list_task(user_id:str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, text, done, created_at FROM tasks WHERE user_id = ? ORDER BY id", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1], "done": bool(r[2]), "created_at": r[3]} for r in rows]

def get_task(user_id: str, task_id: int) -> Optional[dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, text, done, created_at FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return{"id": r[0], "text": r[1], "done": bool(r[2]), "created_at": r[3]}

def edit_task(user_id: str, task_id: int, new_text: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET text = ? WHERE user_id = ? AND id = ?", (new_text, user_id, task_id))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0

def delete_task(user_id: str, task_id: int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0

def set_task_done(user_id: str, task_id: int, done: bool) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done = ? WHERE user_id = ? AND id = ?", (1 if done else 0, user_id, task_id))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0

def add_reminder(user_id: str, task_id: Optional[int], remind_at: str, repeat: Optional[str] = None) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO reminders (user_id, task_id, remind_at, sent, repeat) VALUES (?, ?, ?, 0, ?)",
                (user_id, task_id, remind_at, repeat))
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid

def list_reminders(user_id: str) -> list[dict[str, Any]]:
    conn= _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, task_id, remind_at, sent, repeat FROM reminders WHERE user_id = ? ORDER BY remind_at", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return[{"id": r[0], "task_id": r[1], "remind_at": r[2], "sent": bool(r[3]), "repeat": r[4]} for r in rows]

def delete_reminder(reminder_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0

def mark_reminder_sent(reminder_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


def update_reminder_time(reminder_id: int, new_remind_at: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET remind_at = ?, sent = 0 WHERE id = ?", (new_remind_at, reminder_id))
    conn.commit()
    conn.close()

def pending_reminders() -> list[Dict[str,Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, task_id, remind_at, repeat FROM reminders WHERE sent = 0")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "user_id": r[1], "task_id": r[2], "remind_at": r[3], "repeat": r[4]} for r in rows]
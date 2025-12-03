from datetime import datetime
from typing import List, Optional, Dict, Any
import database

def now_iso():
    return datetime.utcnow().isoformat(timespec='minutes')

def add_task_for_user(user_id: str, text: str) -> int:
    created_at = now_iso()
    return database.add_task(user_id, text, created_at)

def list_task_for_user(user_id: str) -> List[Dict[str, Any]]:
    return database.list_task(user_id)

# backward-compatible aliases expected by bot.py
def list_tasks_for_user(user_id: str) -> List[Dict[str, Any]]:
    return list_task_for_user(user_id)

def edit_task_for_user(user_id: str, task_id: int, new_task: str) -> bool:
    return database.edit_task(user_id, task_id, new_task)

def delete_task_for_user(user_id: str, task_id: int) -> bool:
    return database.delete_task(user_id, task_id)

def complete_task_for_user(user_id: str, task_id: int) -> bool:
    return database.set_task_done(user_id, task_id, True)

def pending_task_for_user(user_id: str, task_id: int) -> bool:
    return database.set_task_done(user_id, task_id, False)

#Reminders
def add_reminder_for_user(user_id: str, remind_at_iso: str, task_id: Optional[int] = None, repeat: Optional[str] = None) -> int:
    return database.add_reminder(user_id, task_id, remind_at_iso, repeat)

def list_reminder_for_user(user_id: str):
    return database.list_reminders(user_id)

def list_reminders_for_user(user_id: str):
    return list_reminder_for_user(user_id)

def delete_reminder_by_id(reminder_id: int) -> bool:
    return database.delete_reminder(reminder_id)

def get_pending_reminders():
    return database.pending_reminders()
from datetime import datetime, timezone, timedelta
import asyncio
import database

# job callback (async)
async def _reminder_callback(context):
    # context.job.data is the reminder dict passed when scheduled
    job = context.job
    rem = job.data  # dict with id, user_id, task_id, remind_at
    chat_id = int(rem["user_id"])
    reminder_id = rem["id"]

    # build message
    if rem.get("task_id"):
        task = database.get_task(rem["user_id"], rem["task_id"])
        task_text = task["text"] if task else "Tarea (eliminada)"
        text = f"⏰ Recordatorio: {task_text}"
    else:
        text = f"⏰ Recordatorio programado."

    # send message
    try:
        await context.bot.send_message(chat_id=chat_id, text=text)
    except Exception:
        # si falla el envío, aún marcamos como enviado para no reintentar infinito
        pass

    # manejar repetición: si tiene 'repeat' no marcamos como enviado definitivamente,
    # actualizamos la próxima fecha; si no tiene repeat, marcamos como enviado
    repeat = rem.get("repeat")
    if repeat in ("daily", "weekly"):
        try:
            # calcular siguiente ocurrencia
            s = rem["remind_at"].strip().replace(" ", "T")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if repeat == "daily":
                next_dt = dt + timedelta(days=1)
            else:
                next_dt = dt + timedelta(weeks=1)
            # guardar próxima fecha en DB (ISO format)
            next_iso = next_dt.isoformat()
            database.update_reminder_time(reminder_id, next_iso)
        except Exception:
            # si hay error calculando, marcar como enviado para evitar bucle
            database.mark_reminder_sent(reminder_id)
    else:
        # marcar como enviado
        database.mark_reminder_sent(reminder_id)


def schedule_pending_reminders(app):
    """
    Lee recordatorios pendientes de DB y los programa en job_queue.
    Debe llamarse después de crear app (para acceder a app.job_queue).
    """
    pending = database.pending_reminders()
    now = datetime.utcnow().replace(tzinfo=timezone.utc)

    for rem in pending:
        try:
            # Parse remind_at (we expect ISO-like string, aceptamos espacio o 'T')
            s = rem["remind_at"].strip().replace(" ", "T")
            dt = datetime.fromisoformat(s)
            # Si no tiene tzinfo, asumimos UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delay = (dt - now).total_seconds()
            if delay < 0:
                delay = 1  # ejecutar pronto si ya pasó
        except Exception:
            # formato inválido -> marcar como enviado para no bloquear
            database.mark_reminder_sent(rem["id"])
            continue

        # programar job
        app.job_queue.run_once(_reminder_callback, when=delay, data=rem)
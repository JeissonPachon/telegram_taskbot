import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import InvalidToken
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import database
import task_manager
import reminders
from datetime import datetime

# Inicializa DB
database.init_db()

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola — soy RecordedTaskBot. Usa /menu o /help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/addtask <texto> - agregar tarea\n"
        "/listtasks - listar tareas\n"
        "/edittask <num> <texto> - editar\n"
        "/deletetask <num> - eliminar\n"
        "/complete <num> - marcar completada\n"
        "/pending <num> - marcar pendiente\n"
        "/addreminder <YYYY-MM-DD HH:MM> [<task_id>] - crear recordatorio\n"
        "/listreminders - ver recordatorios\n"
        "/deletereminder <id> - eliminar recordatorio\n"
        "/menu - abrir menú\n"
    )

# ADD TASK
async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Uso: /addtask Comprar pan")
        return
    tid = task_manager.add_task_for_user(user_id, text)
    await update.message.reply_text(f"Tarea agregada (id={tid}): {text}")

# LIST TASKS (compatible con buttons)
async def listtasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # detect source
    if update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        msg = update.callback_query.message
    else:
        user_id = str(update.message.from_user.id)
        msg = update.message

    rows = task_manager.list_tasks_for_user(user_id)
    if not rows:
        await msg.reply_text("No tienes tareas.")
        return

    text = "📋 *Tus tareas:*\n\n"
    for r in rows:
        estado = "✅" if r["done"] else "⏳"
        text += f"{r['id']}. {estado} {r['text']}\n"
    await msg.reply_text(text, parse_mode="Markdown")

# EDIT TASK
async def edittask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /edittask <num> <nuevo texto>")
        return
    try:
        num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Número inválido")
        return
    new_text = " ".join(context.args[1:])
    ok = task_manager.edit_task_for_user(user_id, num, new_text)
    if ok:
        await update.message.reply_text(f"Tarea #{num} actualizada.")
    else:
        await update.message.reply_text("No se encontró la tarea.")

# DELETE TASK
async def deletetask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /deletetask <num>")
        return
    try:
        num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Número inválido")
        return
    ok = task_manager.delete_task_for_user(user_id, num)
    if ok:
        await update.message.reply_text(f"Tarea #{num} eliminada.")
    else:
        await update.message.reply_text("No se encontró la tarea.")

# COMPLETE / PENDING
async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /complete <num>")
        return
    try:
        num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Número inválido")
        return
    ok = task_manager.complete_task_for_user(user_id, num)
    if ok:
        await update.message.reply_text(f"Tarea #{num} marcada como completada.")
    else:
        await update.message.reply_text("No se encontró la tarea.")

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /pending <num>")
        return
    try:
        num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Número inválido")
        return
    ok = task_manager.pending_task_for_user(user_id, num)
    if ok:
        await update.message.reply_text(f"Tarea #{num} marcada como pendiente.")
    else:
        await update.message.reply_text("No se encontró la tarea.")

# REMINDERS: addreminder <YYYY-MM-DD HH:MM> [task_id]
async def addreminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /addreminder <YYYY-MM-DD HH:MM> [<task_id>]")
        return
    dt_raw = context.args[0]
    # si hay espacio entre fecha-hora, el usuario puede haber puesto más args; soportamos: /addreminder 2025-11-30 17:30  (args separados)
    if len(context.args) >= 2 and ":" in context.args[1]:
        dt_raw = f"{context.args[0]}T{context.args[1]}"
        rest = context.args[2:]
    else:
        rest = context.args[1:]
    # analizar opcionales en `rest`: puede incluir task_id y/o repetición (daily|weekly)
    task_id = None
    repeat = None
    if rest:
        # detectar token de repetición si existe
        for i, tok in enumerate(list(rest)):
            if tok.lower() in ("daily", "weekly"):
                repeat = tok.lower()
                # eliminar ese token de la lista
                rest.pop(i)
                break
        # intentar parsear task_id si queda
        if rest:
            try:
                task_id = int(rest[0])
            except Exception:
                task_id = None

    # normalizar formato (replace space with T)
    dt_iso = dt_raw.strip().replace(" ", "T")
    # validate
    try:
        # if missing seconds it's fine
        _ = datetime.fromisoformat(dt_iso)
    except Exception:
        await update.message.reply_text("Formato de fecha inválido. Usa: YYYY-MM-DD HH:MM")
        return

    rid = task_manager.add_reminder_for_user(user_id, dt_iso, task_id, repeat)
    await update.message.reply_text(f"Recordatorio creado (id={rid}) para {dt_iso}")

    # schedule immediately in job_queue
    # job data used by reminders._reminder_callback expects dict with id,user_id,task_id,remind_at
    app = context.application
    rem_row = {"id": rid, "user_id": user_id, "task_id": task_id, "remind_at": dt_iso, "repeat": repeat}
    # compute delay and schedule via reminders module (reuse its logic)
    reminders.schedule_pending_reminders(app)  # quick and safe: re-schedule all pending (lightweight for small scale)

async def listreminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    rows = task_manager.list_reminders_for_user(user_id)
    if not rows:
        await update.message.reply_text("No tienes recordatorios.")
        return
    text = "🔔 *Tus recordatorios:*\n\n"
    for r in rows:
        text += f"{r['id']}. {r['remind_at']} (task_id={r['task_id']}) sent={r['sent']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def deletereminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /deletereminder <id>")
        return
    try:
        rid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Id inválido.")
        return
    ok = task_manager.delete_reminder_by_id(rid)
    if ok:
        await update.message.reply_text(f"Recordatorio {rid} eliminado.")
    else:
        await update.message.reply_text("No encontrado.")

# MENU (botones básicos)
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Agregar tarea", callback_data="addtask_menu")],
        [InlineKeyboardButton("📋 Ver tareas", callback_data="listtasks_menu")],
        [InlineKeyboardButton("📝 Editar tarea", callback_data="edit_menu")],
        [InlineKeyboardButton("❌ Eliminar tarea", callback_data="delete_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "addtask_menu":
        await query.message.reply_text("Escribe tu tarea con /addtask <texto>")
    elif data == "listtasks_menu":
        await listtasks(update, context)
    elif data == "edit_menu":
        await query.message.reply_text("Usa /edittask <num> <texto>")
    elif data == "delete_menu":
        await query.message.reply_text("Usa /deletetask <num>")

# Optional message handler: simple echo (you can use it to handle interactive edit flows)
async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # we keep it empty or use to capture free text when implementing interactive flows
    return

# ---------- MAIN ----------
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("ERROR: Set TELEGRAM_TOKEN env var")
        return

    # Basic token sanity check
    if ":" not in token or not token.split(":")[0].isdigit():
        print("ERROR: TELEGRAM_TOKEN parece no tener el formato correcto. Comprueba tu token en BotFather.")
        return

    # Build application (initialization may still fail if token is invalid/revoked)
    app = ApplicationBuilder().token(token).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CommandHandler("listtasks", listtasks))
    app.add_handler(CommandHandler("edittask", edittask))
    app.add_handler(CommandHandler("deletetask", deletetask))
    app.add_handler(CommandHandler("complete", complete))
    app.add_handler(CommandHandler("pending", pending))

    app.add_handler(CommandHandler("addreminder", addreminder))
    app.add_handler(CommandHandler("listreminders", listreminders))
    app.add_handler(CommandHandler("deletereminder", deletereminder))

    # menu & callback
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(menu_handler))

    # message handler (for extension / interactive flows)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_text))

    # schedule pending reminders (needs the app.job_queue available)
    # IMPORTANT: schedule after building app but before run_polling
    reminders.schedule_pending_reminders(app)

    print("Bot iniciado...")
    try:
        app.run_polling()
    except InvalidToken:
        print("ERROR: El token fue rechazado por Telegram (InvalidToken). Genera uno nuevo con BotFather y actualiza la variable TELEGRAM_TOKEN.")
    except Exception as e:
        print("ERROR: El bot falló al iniciar:", e)

if __name__ == "__main__":
    main()
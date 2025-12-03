# RecordedTaskBot

Bot de Telegram para gestionar tareas y recordatorios con soporte para repeticiones diarias y semanales.

## Instalación local

```bash
pip install -r requirements.txt
```

## Variables de entorno

Crea un archivo `.env` o configura en tu sistema:

```
TELEGRAM_TOKEN=tu_token_aqui
```

## Ejecutar localmente

```bash
python bot.py
```

## Desplegar en Railway

1. **Conecta tu repositorio GitHub a Railway**
2. **Configura las variables de entorno en Railway:**
   - `TELEGRAM_TOKEN`: Tu token de BotFather
3. **Railway automáticamente:**
   - Lee `Procfile` y ejecuta `python bot.py`
   - Instala dependencias desde `requirements.txt`

## Comandos disponibles

- `/start` - Inicia el bot
- `/help` - Muestra comandos disponibles
- `/addtask <texto>` - Agregar tarea
- `/listtasks` - Ver tareas
- `/edittask <num> <texto>` - Editar tarea
- `/deletetask <num>` - Eliminar tarea
- `/complete <num>` - Marcar completada
- `/pending <num>` - Marcar pendiente
- `/addreminder <YYYY-MM-DD HH:MM> [task_id] [daily|weekly]` - Crear recordatorio
- `/listreminders` - Ver recordatorios
- `/deletereminder <id>` - Eliminar recordatorio
- `/menu` - Menú de opciones

## Recordatorios recurrentes

Ejemplos:
```
/addreminder 2025-12-03 18:00           # Recordatorio único
/addreminder 2025-12-03 18:00 daily     # Diario
/addreminder 2025-12-03 18:00 weekly    # Semanal
/addreminder 2025-12-03 18:00 5 daily   # Diario para la tarea 5
```

## Base de datos

- **Local:** SQLite en `data/tasks.db`
- **Railway:** SQLite en `/tmp/tasks.db` (volumen temporal)

## Autor

RecordedTaskBot

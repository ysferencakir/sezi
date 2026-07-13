from datetime import date, timedelta

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from core.config import settings
from modules.context import service

FEELING, NOTES, EVENTS = range(3)

_application: Application | None = None


def _current_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


async def _start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton(str(n), callback_data=str(n)) for n in range(1, 6)],
        [InlineKeyboardButton(str(n), callback_data=str(n)) for n in range(6, 11)],
    ]
    await update.message.reply_text(
        "Bu hafta genel olarak nasıl hissettin? (1-10)",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return FEELING


async def _feeling_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ctx.user_data["general_feeling"] = int(query.data)
    await query.edit_message_text(f"Seçilen: {query.data}/10\n\nBu hafta ne oldu? Kısa bir not yaz.")
    return NOTES


async def _notes_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["notes"] = update.message.text
    await update.message.reply_text("Özel bir olay var mıydı? (sınav, hastalık, seyahat vb.) Yoksa /skip yaz.")
    return EVENTS


async def _events_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["special_events"] = update.message.text
    await _save(update, ctx)
    return ConversationHandler.END


async def _events_skipped(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["special_events"] = None
    await _save(update, ctx)
    return ConversationHandler.END


async def _save(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    week_start = _current_week_start()
    await service.submit_context(
        week_start=week_start,
        notes=ctx.user_data.get("notes", ""),
        special_events=ctx.user_data.get("special_events"),
        general_feeling=ctx.user_data.get("general_feeling"),
    )
    await update.message.reply_text(f"Kaydedildi ✅ (hafta: {week_start})")


async def _cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("İptal edildi.")
    return ConversationHandler.END


def _build_application() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("context", _start)],
        states={
            FEELING: [CallbackQueryHandler(_feeling_chosen)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, _notes_received)],
            EVENTS: [
                CommandHandler("skip", _events_skipped),
                MessageHandler(filters.TEXT & ~filters.COMMAND, _events_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )
    app.add_handler(conv)
    return app


async def start() -> None:
    """Start Telegram bot polling as a background task within the FastAPI event loop."""
    global _application
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token yok — interaktif bot devre dışı")
        return

    _application = _build_application()
    await _application.initialize()
    await _application.start()
    await _application.updater.start_polling()
    logger.info("Telegram bot polling başladı (/context komutu aktif)")


async def stop() -> None:
    if _application is None:
        return
    await _application.updater.stop()
    await _application.stop()
    await _application.shutdown()
    logger.info("Telegram bot durduruldu")

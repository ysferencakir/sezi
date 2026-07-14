import asyncio
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
from modules.smoking import service as smoking_service
from modules.transit import eshot_scraper, izmir_transit
from modules.transit.routes import ROUTES
from modules.weather import location_service

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
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
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


async def _location_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Tekil ya da canlı konum paylaşımını yakalar.

    Canlı konum güncellemeleri Telegram'dan `edited_message` olarak gelir
    (update.message boş olur), bu yüzden effective_message kullanılıyor.
    """
    message = update.effective_message
    loc = message.location
    await location_service.update_location(latitude=loc.latitude, longitude=loc.longitude)
    if loc.live_period:
        return  # canlı konum güncellemelerinde her seferinde onay mesajı gönderme
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await message.reply_text("Konum kaydedildi 📍 — hava durumu bu konuma göre çekilecek.")


async def _smoke_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(str(n), callback_data=f"smoke:{n}") for n in range(1, 11)],
        [InlineKeyboardButton(str(n), callback_data=f"smoke:{n}") for n in range(11, 21)],
    ]
    await update.message.reply_text(
        "Bugün kaç sigara içtin?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _smoke_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    count = int(query.data.split(":")[1])
    await smoking_service.submit_count(day=date.today(), count=count)
    await query.edit_message_text(f"Kaydedildi ✅ — bugün: {count}")


async def _fetch_route_arrivals(route: dict) -> list[dict]:
    """ESHOT'un resmi sitesinden gerçek mesafe/süre ile yaklaşan otobüsleri çeker
    (bkz. eshot_scraper.py — site scraping, resmi public API'de bu veri yok).
    Sorun çıkarsa sessizce boş döner — /otobus komutu o bacağı 'veri yok' gösterir."""
    hat_ids = route.get("hat_ids") or []
    try:
        rows = await eshot_scraper.fetch_arrivals(route["durak_id"], hat_ids[0], route["hat_yon"])
    except Exception as exc:
        logger.warning(f"[transit] {route['label']} sorgusu başarısız: {type(exc).__name__}: {exc!r}")
        return []
    return [r for r in rows if not hat_ids or r["hat"] in hat_ids]


async def _nearby_stops(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    location = await location_service.get_location()
    if location is None:
        await update.message.reply_text(
            "Henüz konum kaydedilmemiş — bota Telegram konumunu paylaş (📎 → Location)."
        )
        return

    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        stops = await izmir_transit.fetch_nearby_stops(location.latitude, location.longitude)
    except Exception as exc:
        logger.exception("[transit] yakın durak sorgusu başarısız")
        await update.message.reply_text(f"Yakın durak bilgisi alınamadı: {exc}")
        return

    if not stops:
        await update.message.reply_text("Yakında durak bulunamadı.")
        return

    lines = ["<b>📍 Yakındaki Duraklar</b>", "<pre>"]
    for stop in stops[:5]:
        mesafe = stop.get("mesafe")
        mesafe_str = f"{mesafe:.0f} m" if mesafe is not None else "-"
        adi = (stop.get("adi") or "")[:28]
        lines.append(f"{adi:<28} {mesafe_str:>6}  #{stop.get('durakId')}")
    lines.append("</pre>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


def _tr_title(text: str) -> str:
    """TÜM BÜYÜK HARFLİ hat adlarını okunur bir 'Title Case' hale getirir."""
    _lower_map = str.maketrans("IİÇĞÖŞÜ", "ıiçğöşü")
    _upper_first = {"i": "İ", "ı": "I"}

    words = []
    for word in text.strip().split(" "):
        if not word:
            continue
        lowered = word.translate(_lower_map).lower()
        first = _upper_first.get(lowered[0], lowered[0].upper())
        words.append(first + lowered[1:])
    return " ".join(words)


def _short_mesafe(mesafe: str) -> str:
    return mesafe.replace(" metre", " m")


def _format_arrivals_table(arrivals: list[dict]) -> str:
    """Hat/mesafe/süreyi hizalı, monospace bir tabloya dönüştürür."""
    header = f"{'Hat':<5}{'Mesafe':>9}   {'Süre':<10}"
    row_lines = [header, "-" * len(header)]
    for row in arrivals:
        if row["at_stop"]:
            row_lines.append(f"{row['hat']:<5}{'🔴 Durakta':>9}")
        else:
            row_lines.append(f"{row['hat']:<5}{_short_mesafe(row['mesafe']):>9}   {row['sure']:<10}")
    return "<pre>" + "\n".join(row_lines) + "</pre>"


async def _send_route_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE, routes: list[dict], title: str) -> None:
    await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # ESHOT sitesi art arda hızlı isteklerde sorun çıkarabiliyor —
    # güvenilirlik için sıralı ve aralıklı çekiliyor (hız kritik değil).
    results = []
    for route in routes:
        results.append(await _fetch_route_arrivals(route))
        await asyncio.sleep(0.3)

    lines = [f"<b>{title}</b>"]
    for route, arrivals in zip(routes, results):
        lines.append(f"\n<b>{route['label']}</b>")
        if not arrivals:
            lines.append("<i>Yaklaşan otobüs yok</i>")
            continue

        # Aynı hatta birden fazla fiziksel otobüs aynı mesafe/süreyi gösterebiliyor —
        # tekrar tekrar aynı satırı göstermemek için tekilleştirip en yakın 3'ü listeliyoruz.
        seen = set()
        unique_arrivals = []
        for row in arrivals:
            key = (row["hat"], row["mesafe"], row["sure"])
            if key in seen:
                continue
            seen.add(key)
            unique_arrivals.append({**row, "hat_adi": _tr_title(row["hat_adi"])})

        # Aynı bacaktaki farklı hatlar için (ör. 268 ve 368) hat adını bir kez başlık olarak yaz.
        by_line: dict[str, list[dict]] = {}
        for row in unique_arrivals[:6]:
            by_line.setdefault(row["hat_adi"], []).append(row)

        for hat_adi, rows in by_line.items():
            lines.append(f"<i>{hat_adi}</i>")
            lines.append(_format_arrivals_table(rows[:3]))

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def _bus_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_route_status(update, ctx, ROUTES, "🚌 Güzergah Durumu")


async def _office_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    routes = [r for r in ROUTES if r["direction"] == "ofis"]
    await _send_route_status(update, ctx, routes, "🏢 Ofise Gidiş")


async def _dorm_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    routes = [r for r in ROUTES if r["direction"] == "yurt"]
    await _send_route_status(update, ctx, routes, "🏠 Yurda Dönüş")


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
    app.add_handler(CommandHandler("sigara", _smoke_start))
    app.add_handler(CallbackQueryHandler(_smoke_chosen, pattern=r"^smoke:"))
    app.add_handler(MessageHandler(filters.LOCATION, _location_received))
    app.add_handler(CommandHandler("otobus", _bus_status))
    app.add_handler(CommandHandler("ofis", _office_status))
    app.add_handler(CommandHandler("yurt", _dorm_status))
    app.add_handler(CommandHandler("yakindurak", _nearby_stops))
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

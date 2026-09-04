# /srv/dj-stream/app/bot.py
from __future__ import annotations
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app import config, db, energy, genres
from app.bot_voting_handlers import upvote, downvote, moreenergy, lessenergy, community

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("acid-prophet")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    e = db.get_energy()
    g = db.get_genre()
    mood = energy.energy_to_mood(e)
    color = energy.energy_to_color(e)
    display = genres.genre_display(g)
    text = (
        f"⚡ *ACID PROPHET ONLINE*\n\n"
        f"Energy: *{e}/10*\n"
        f"Genre: *{display}*\n"
        f"Mood: *{mood}*\n"
        f"Color: `{color}`\n\n"
        f"Commands:\n"
        f"/energy 1-10\n"
        f"/genre +1 | /genre -1\n"
        f"/upvote  /downvote\n"
        f"/moreenergy  /lessenergy\n"
        f"/status  /help"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    e = db.get_energy()
    g = db.get_genre()
    info = genres.get_genre_info(g) or {}
    bpm = ""
    if "bpm_min" in info and "bpm_max" in info:
        bpm = f"\nBPM: {info['bpm_min']}–{info['bpm_max']}"
    text = (
        f"⚡ *Status*\n"
        f"Energy: {e}/10 → {energy.energy_to_mood(e)}\n"
        f"Genre: {genres.genre_display(g)}{bpm}\n"
        f"Color: {energy.energy_to_color(e)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def energy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /energy 1-10")
        return
    try:
        n = int(context.args[0])
        if not 1 <= n <= 10:
            raise ValueError
        db.set_energy(n)
        await update.message.reply_text(
            f"Energy → *{n}/10*\n"
            f"Mood: {energy.energy_to_mood(n)}\n"
            f"Color: `{energy.energy_to_color(n)}`",
            parse_mode="Markdown",
        )
    except (ValueError, TypeError):
        await update.message.reply_text("Nur ganze Zahlen 1–10 erlaubt.")


async def genre_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or context.args[0] not in ("+1", "-1"):
        await update.message.reply_text("Usage: /genre +1  oder  /genre -1")
        return
    delta = 1 if context.args[0] == "+1" else -1
    current = db.get_genre()
    new = genres.next_genre(current, delta)
    db.set_genre(new)
    info = genres.get_genre_info(new) or {}
    e = info.get("energy", db.get_energy())
    # Optional: Energy an Genre anpassen (kann später als Preference gesteuert werden)
    text = (
        f"Genre → *{genres.genre_display(new)}*\n"
        f"Energy-Band: {e}/10\n"
        f"Mood: {', '.join(info.get('mood', []))}\n"
        f"BPM: {info.get('bpm_min', '?')}–{info.get('bpm_max', '?')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def upvote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db.record_vote(user.id, update.effective_chat.id if update.effective_chat else None,
                   "up", db.get_energy(), db.get_genre())
    await update.message.reply_text("▲ Upvote registered")


async def downvote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db.record_vote(user.id, update.effective_chat.id if update.effective_chat else None,
                   "down", db.get_energy(), db.get_genre())
    await update.message.reply_text("▼ Downvote registered")


async def moreenergy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db.record_vote(user.id, update.effective_chat.id if update.effective_chat else None,
                   "more_energy", db.get_energy(), db.get_genre())
    await update.message.reply_text("⚡ More energy registered")


async def lessenergy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db.record_vote(user.id, update.effective_chat.id if update.effective_chat else None,
                   "less_energy", db.get_energy(), db.get_genre())
    await update.message.reply_text("🌙 Less energy registered")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "*Acid Prophet Commands*\n\n"
        "/start – Status + Begrüßung\n"
        "/status – Aktuelle Energy / Genre / Mood\n"
        "/energy 1-10 – Energy setzen\n"
        "/genre +1 | /genre -1 – Genre navigieren\n"
        "/upvote /downvote – Track bewerten\n"
        "/moreenergy /lessenergy – Energy-Druck\n"
        "/community – Community Snapshot\n"
        "/help – Diese Hilfe"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN missing in .env")

    db.init_db()
    if db.get_state("energy") is None:
        db.set_energy(7)
    if db.get_state("genre") is None:
        db.set_genre("psytrance")

    problems = genres.validate_catalog()
    if problems:
        log.warning("Genre catalog issues: %s", problems)

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("energy", energy_cmd))
    app.add_handler(CommandHandler("genre", genre_cmd))
    app.add_handler(CommandHandler("upvote", upvote))
    app.add_handler(CommandHandler("downvote", downvote))
    app.add_handler(CommandHandler("moreenergy", moreenergy))
    app.add_handler(CommandHandler("lessenergy", lessenergy))
    app.add_handler(CommandHandler("community", community))
    app.add_handler(CommandHandler("help", help_cmd))

    log.info("Acid Prophet starting (no secrets logged)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

# /srv/dj-stream/app/bot_voting_handlers.py
"""
Drop-in Replacement / Erweiterung für die Voting-Handler in bot.py

Einfach die vier Handler-Funktionen in bot.py ersetzen
oder dieses Modul importieren und die Handler registrieren.
"""
from __future__ import annotations

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app import voting

log = logging.getLogger("acid-prophet.bot")


async def upvote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    result = voting.record_and_process(
        user_id=user.id,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        vote_type="up",
    )
    await update.message.reply_text(result.message, parse_mode="Markdown")


async def downvote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    result = voting.record_and_process(
        user_id=user.id,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        vote_type="down",
    )
    await update.message.reply_text(result.message, parse_mode="Markdown")


async def moreenergy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    result = voting.record_and_process(
        user_id=user.id,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        vote_type="more_energy",
    )
    await update.message.reply_text(result.message, parse_mode="Markdown")


async def lessenergy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    result = voting.record_and_process(
        user_id=user.id,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        vote_type="less_energy",
    )
    await update.message.reply_text(result.message, parse_mode="Markdown")


async def community(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/community – zeigt aktuellen Community-Snapshot."""
    snap = voting.compute_community_snapshot()
    profile = voting.build_community_profile(limit=100)

    lines = [
        "📊 *Community Snapshot*",
        f"Fenster: letzte {snap.window_minutes} min",
        f"Votes: {snap.total_votes}",
        f"▲ {snap.up}   ▼ {snap.down}",
        f"⚡ {snap.more_energy}   🌙 {snap.less_energy}",
        f"Energy-Pressure: `{snap.energy_pressure:+.2f}`",
        f"Track-Score: `{snap.track_score:.2f}`",
    ]
    if snap.dominant_genre:
        lines.append(f"Dominantes Genre: *{snap.dominant_genre}*")
    if snap.suggested_energy is not None:
        lines.append(f"Vorschlag Energy: *{snap.suggested_energy}/10*")
    if profile.get("preferred_energy"):
        lines.append(f"Langzeit-Präferenz Energy: *{profile['preferred_energy']}/10*")
    if profile.get("preferred_genre"):
        lines.append(f"Langzeit-Präferenz Genre: *{profile['preferred_genre']}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

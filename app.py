import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- CONFIG ---------------- #
BOT_TOKEN = os.getenv(
    "8499529604:AAGoKp_oalDoWoa8Wy8SPFwqpel81SJym9A") or "8499529604:AAGoKp_oalDoWoa8Wy8SPFwqpel81SJym9A"
PRIVATE_CHANNEL_ID = -1002915940030
REQUIRED_CHANNELS = ["@CartoonNetwork02", "@AnimeNetwork02"]

SHOWS = {
    "bc_s1": {"title": "Black Clover — Season 1", "message_ids": list(range(2, 54))},
    "bc_s2": {"title": "Black Clover — Season 2", "message_ids": list(range(54, 102))},
    "at_s1": {"title": "Adventure Time — Season 1", "message_ids": list(range(102, 130))},
    "at_s2": {"title": "Adventure Time — Season 2", "message_ids": list(range(130, 157))},
}
# ----------------------------------------- #

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_missing_channels(bot, user_id):
    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in (
                    ChatMemberStatus.MEMBER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.OWNER,
            ):
                missing.append(ch)
        except Exception as e:
            logger.info(f"get_chat_member error for {ch} and user {user_id}: {e}")
            missing.append(ch)
    return missing


async def prompt_join(update_or_query, context: ContextTypes.DEFAULT_TYPE, missing_channels):
    keyboard = []
    for ch in missing_channels:
        if ch == "@CartoonNetwork02":
            friendly_name = "Cartoon Network"
        elif ch == "@AnimeNetwork02":
            friendly_name = "Anime Network"
        else:
            friendly_name = ch.lstrip("@")
        keyboard.append([InlineKeyboardButton(f"Join {friendly_name}", url=f"https://t.me/{ch.lstrip('@')}")])

    keyboard.append([InlineKeyboardButton("✅ Check", callback_data="check_join")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text_lines = [
        f"🔒 Hi {update_or_query.effective_user.first_name}! To unlock this season, please join the required channels:"]
    for ch in missing_channels:
        if ch == "@CartoonNetwork02":
            text_lines.append("• Cartoon Network")
        elif ch == "@AnimeNetwork02":
            text_lines.append("• Anime Network")

    text = "\n".join(text_lines)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)


async def send_season_episodes(bot, chat_id, season_key):
    show = SHOWS.get(season_key)
    if not show:
        await bot.send_message(chat_id=chat_id, text="❌ Season not found.")
        return
    title = show["title"]
    await bot.send_message(chat_id=chat_id, text=f"📺 Sending {title} — please wait...")
    for msg_id in show["message_ids"]:
        try:
            await bot.copy_message(chat_id=chat_id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=msg_id)
        except Exception as e:
            logger.error(f"Error sending message {msg_id}: {e}")
    await bot.send_message(chat_id=chat_id, text=f"✅ All episodes of {title} sent!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args:
        text = "👋 Welcome! To get a season, use the special season links posted in the channel.\n\nAvailable seasons:\n"
        for k, v in SHOWS.items():
            text += f"• {v['title']} — key: {k}\n"
        text += "\nOr click your channel's season link which opens this bot.\n"
        await update.message.reply_text(text)
        return

    season_key = args[0]
    if season_key not in SHOWS:
        await update.message.reply_text("❌ Invalid season link.")
        return

    context.user_data["requested_season"] = season_key
    missing = await get_missing_channels(context.bot, user.id)
    if not missing:
        await send_season_episodes(context.bot, user.id, season_key)
        return

    await prompt_join(update, context, missing)


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    season_key = context.user_data.get("requested_season")
    if not season_key:
        await query.edit_message_text("⚠️ No requested season found. Please reopen the season link.")
        return

    missing = await get_missing_channels(context.bot, user.id)
    if not missing:
        await query.edit_message_text("✅ Verified! Sending episodes now...")
        await send_season_episodes(context.bot, user.id, season_key)
    else:
        
        keyboard = []
        for ch in missing:
            if ch == "@CartoonNetwork02":
                friendly_name = "Cartoon Network"
            elif ch == "@AnimeNetwork02":
                friendly_name = "Anime Network"
            else:
                friendly_name = ch.lstrip("@")
            keyboard.append([InlineKeyboardButton(f"Join {friendly_name}", url=f"https://t.me/{ch.lstrip('@')}")])
        keyboard.append([InlineKeyboardButton("✅ Check", callback_data="check_join")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        text_lines = [f"❌ You still need to join the following:"]
        for ch in missing:
            if ch == "@CartoonNetwork02":
                text_lines.append("• Cartoon Network")
            elif ch == "@AnimeNetwork02":
                text_lines.append("• Anime Network")
        text = "\n".join(text_lines)

        await query.edit_message_text(text=text, reply_markup=reply_markup)


def main():
    BOT_TOKEN = os.environ.get("API_TOKEN")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set.  Set the API_TOKEN environment variable.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))

    PORT = int(os.environ.get("PORT", "8443"))
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

    if not RENDER_EXTERNAL_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL not set. Set the RENDER_EXTERNAL_URL environment variable in Render.")

    logger.info(f"Starting webhook on port {PORT} with webhook URL {RENDER_EXTERNAL_URL}")


    app.run_webhook(listen="0.0.0.0",
                      port=PORT,
                      webhook_url=RENDER_EXTERNAL_URL)



if __name__ == "__main__": 
    main()


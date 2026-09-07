from __future__ import annotations

import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(f"Chat ID: {update.message.chat_id}")


async def get_message_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if update.message.reply_to_message:
        await update.message.reply_text(
            f"Message ID: {update.message.reply_to_message.message_id}"
        )
    else:
        await update.message.reply_text("Reply to a message with /getid.")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the helper bot.")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("getchatid", get_chat_id))
    application.add_handler(
        CommandHandler("getid", get_message_id, filters=filters.REPLY)
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

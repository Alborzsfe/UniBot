import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Replace with your bot's token
TOKEN = '7315845497:AAG-LoBEIycyDPNCIbtZmoah6JdchdtqZ_8'

# These will be filled in later during setup
GROUP_CHAT_ID = -1002660444971  # e.g., -1001234567890
FILE_MESSAGE_IDS = [39, 47]  # e.g., [1234, 5678] – list of message IDs to forward

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat.type == 'private':
        if not GROUP_CHAT_ID or not FILE_MESSAGE_IDS:
            await update.message.reply_text('Bot setup incomplete. Contact the admin.')
            return
        for msg_id in FILE_MESSAGE_IDS:
            try:
                await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=GROUP_CHAT_ID,
                    message_id=msg_id
                )
            except Exception as e:
                logging.error(f'Error forwarding message {msg_id}: {e}')
        await update.message.reply_text('Files forwarded successfully!')
    else:
        await update.message.reply_text('Please use /start in a private chat with me.')

async def getchatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'This chat ID is: {update.message.chat_id}')

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        replied_msg_id = update.message.reply_to_message.message_id
        await update.message.reply_text(f'The replied message ID is: {replied_msg_id}')
    else:
        await update.message.reply_text('Reply to a message with /getid to get its ID.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Handle /start only in private chats
    application.add_handler(CommandHandler('start', start, filters.ChatType.PRIVATE))
    # Handle /getchatid and /getid in any chat
    application.add_handler(CommandHandler('getchatid', getchatid))
    application.add_handler(CommandHandler('getid', getid))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
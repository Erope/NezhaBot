import logging, sqlite3, datetime, io
import socket
from config import Token

from telegram import Update, ForceReply, message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from tools import checkurl
from nezha import NezhaDashboard

socket.setdefaulttimeout(15)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text('NezhaDashboard Check Bot, command: /checknezha https://ops.naibahq.com/')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('command: /checknezha url, like: /checknezha https://ops.naibahq.com/')


def checknezha(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        context.bot.send_message(chat_id=update.effective_chat.id, text="参数错误，必须为URL，例: /checknezha https://ops.naibahq.com/")
        return
    try:
        url, ws_url = checkurl(context.args[0])
    except BaseException as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
        return
    n = NezhaDashboard(url, ws_url)
    try:
        context.bot.send_message(chat_id=update.effective_chat.id, text=n.collect())
    except BaseException as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
        return
    

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(Token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("checknezha", checknezha, run_async=True))
    dispatcher.add_handler(CommandHandler("nz", checknezha, run_async=True))

    # on non command i.e message - echo the message on Telegram
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
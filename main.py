import logging, sqlite3
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
    update.message.reply_text('NezhaDashboard Check Bot, command: /checknezha /nz /seturl')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('command: /checknezha /nz /seturl, like: /checknezha https://ops.naibahq.com/')

def seturl(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    if len(context.args) != 1:
        update.message.reply_text("参数错误，必须为URL，例: /seturl https://ops.naibahq.com/")
        return
    try:
        url, ws_url = checkurl(context.args[0])
    except BaseException as e:
        update.message.reply_text(str(e))
        return
    n = NezhaDashboard(url, ws_url)
    try:
        n.collect()
    except BaseException as e:
        update.message.reply_text(str(e))
        return
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO DashboardINFO(UID, URL) VALUES(?,?)", (user['id'], context.args[0]))
        conn.commit()
        conn.close()
    except BaseException as e:
        update.message.reply_text(f"数据库出错，{str(e)}")
        return
    update.message.reply_text("成功，您现在可以直接使用 /nz 命令了。")

def nz(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    test_url = ""
    if len(context.args) >= 2:
        update.message.reply_text("参数错误，必须为URL或者无参数，例: /nz https://ops.naibahq.com/")
        return
    elif len(context.args) == 0:
        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("SELECT URL FROM DashboardINFO WHERE UID = ?", (user['id'],))
            values = c.fetchall()
            conn.close()
            if len(values) == 0:
                update.message.reply_text("您尚未添加自己的面板链接，请添加后(使用/seturl命令，建议私聊)或使用参数访问，如 /nz https://ops.naibahq.com/")
                return
            elif len(values) >= 2:
                update.message.reply_text("数据库错误，请联系管理员。")
                return
            test_url = values[0][0]
        except BaseException as e:
            update.message.reply_text(f"数据库出错。错误信息: {str(e)}")
            return
    else:
        test_url = context.args[0]
    try:
        url, ws_url = checkurl(test_url)
    except BaseException as e:
        update.message.reply_text(str(e))
        return
    n = NezhaDashboard(url, ws_url)
    try:
        update.message.reply_text(n.show())
    except BaseException as e:
        if update.message.chat['type'] == 'private':
            update.message.reply_text(str(e))
        else:
            update.message.reply_text("查询出错。群聊中为保护隐私不展现错误信息，请重试或通过私聊重试获取错误信息。")
        return

def checknezha(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("参数错误，必须为URL，例: /checknezha https://ops.naibahq.com/")
        return
    try:
        url, ws_url = checkurl(context.args[0])
    except BaseException as e:
        update.message.reply_text(str(e))
        return
    n = NezhaDashboard(url, ws_url)
    try:
        update.message.reply_text(n.collect())
    except BaseException as e:
        update.message.reply_text(str(e))
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
    dispatcher.add_handler(CommandHandler("nz", nz, run_async=True))
    dispatcher.add_handler(CommandHandler("seturl", seturl, run_async=True))

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
#!/usr/bin/env python3
from telegram.ext import Application, CommandHandler, MessageHandler
from telegram import Update
from telegram.ext import CallbackContext, filters
import logging
import code, ping, wfa, vault, alive, hls
from common import *
from config import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("zhiyb is a bot!")

# Unknown
async def unknown(update: Update, context: CallbackContext):
    print(update)
    msg = None
    if update.message:
        text = update.message.text
        msg = update.message
    elif update.channel_post:
        text = update.channel_post.text
        msg = update.channel_post
    if text == '/chat_id':
        text = f"Chat ID: {update.effective_chat.id}\n{update}"
        await context.bot.send_message(chat_id=chat_id_admin, text=text)
        if msg:
            msg.delete()
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"What is that?")

# General messages
async def echo(update: Update, context: CallbackContext):
    return
    text = "You sent: " + update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():
    app = Application.builder() \
        .base_url(f"{base_url}/bot") \
        .base_file_url(f"{base_url}/file/bot") \
        .local_mode(base_local) \
        .read_timeout(1000).write_timeout(1000) \
        .token(token).build()

    app.add_handler(CommandHandler('start', start))

    code.register(app)
    wfa.register(app)
    vault.register(app)
    alive.register(app)
    hls.register(app)

    ping.register(app)
    for host in ping_hosts:
        ping.target(app, host, chat_id_admin)

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    app.add_handler(echo_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    app.add_handler(unknown_handler)

    job_send_msg(app, chat_id_admin, 'Bot started')
    app.run_polling()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import code, ping, lights_ha, wfa, vault, alive, hls
from config import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="zhiyb is a bot!")

# Unknown
def unknown(update, context):
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
        context.bot.send_message(chat_id=chat_id_admin, text=text)
        if msg:
            msg.delete()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"What is that?")

# General messages
def echo(update, context):
    return
    text = "You sent: " + update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():
    updater = Updater(token=token, base_url=base_url, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('python3', code.tgbot_python3))
    dispatcher.add_handler(CommandHandler('py', code.tgbot_python3))
    dispatcher.add_handler(CommandHandler('run', code.tgbot_run))

    wfa.register(updater)
    vault.register(updater)
    alive.register(updater)
    hls.register(updater)

    for host in ping_hosts:
        ping.Ping(updater, host, chat_id_admin)

    lights_ha.Lights(updater, chat_id_admin)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.bot.send_message(chat_id=chat_id_admin, text='Bot started')
    updater.idle()

if __name__ == '__main__':
    main()

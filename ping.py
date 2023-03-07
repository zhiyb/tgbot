#!/usr/bin/env python3
import platform, subprocess
import traceback
from telegram.constants import ParseMode
from telegram.ext import CommandHandler

__all__ = ["register", "target"]

class Ping:
    host = None
    online = None
    chat_id = 0
    interval = 20

    def __init__(self, app, host, chat_id = 0):
        self.host = host
        self.online = None
        self.chat_id = chat_id
        app.job_queue.run_repeating(self.run, self.interval)

    def ping(host, count = 3):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        https://stackoverflow.com/a/32684938
        """

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower()=='windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, str(count), host]

        return subprocess.call(command) == 0

    def oltext(host, online):
        return f'🌐 _{host}_ online' if online else f'🚫 _{host}_ offline'

    async def run(self, context):
        bot = context.bot
        try:
            now = Ping.ping(self.host)
            if now != self.online:
                self.online = now
                text = Ping.oltext(self.host, self.online)
                await bot.send_message(chat_id=self.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except:
            text = traceback.format_exc(1)
            await bot.send_message(chat_id=self.chat_id, text=text)

    async def cmd(update, context):
        try:
            query = update.message.text
            host = query.split(maxsplit = 1)[1]
            online = Ping.ping(host)
            text = Ping.oltext(host, online)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN)
        except:
            text = traceback.format_exc(1)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def register(app):
    app.add_handler(CommandHandler('ping', Ping.cmd))

def target(app, host, chat_id):
    Ping(app, host, chat_id)

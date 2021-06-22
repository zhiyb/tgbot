#!/usr/bin/env python3
import platform, subprocess
import traceback
from telegram import ParseMode
from telegram.ext import CommandHandler

class Ping:
    host = None
    online = None
    chat_id = 0
    interval = 20

    def __init__(self, updater, host, chat_id = 0):
        self.host = host
        self.online = None
        self.chat_id = chat_id
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler('ping', self.cmd))
        updater.job_queue.run_repeating(self.run, self.interval)

    def ping(self, host, count = 3):
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

    def oltext(self, host, online):
        return f'🌐 _{host}_ online' if online else f'🚫 _{host}_ offline'

    def run(self, context):
        bot = context.bot
        try:
            now = self.ping(self.host)
            if now != self.online:
                self.online = now
                text = self.oltext(self.host, self.online)
                bot.send_message(chat_id=self.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
        except:
            text = traceback.format_exc(1)
            bot.send_message(chat_id=self.chat_id, text=text)

    def cmd(self, update, context):
        try:
            query = update.message.text
            host = query.split(maxsplit = 1)[1]
            online = self.ping(host)
            text = self.oltext(host, online)
            context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN)
        except:
            text = traceback.format_exc(1)
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)

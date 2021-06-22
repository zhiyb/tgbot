#!/usr/bin/env python3
import json
import traceback
import urllib.parse, urllib.request
from telegram import ParseMode
from telegram.ext import CommandHandler

class Lights:
    state = 'off'

    def __init__(self, updater, host, chat_id):
        self.host = host
        self.chat_id = chat_id
        self.msgs = []
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler('l', self.cmd))
        dispatcher.add_handler(CommandHandler('lights', self.cmd))

    def delete_msgs(self):
        for m in self.msgs:
            try:
                m.delete()
            except:
                pass
        self.msgs = []

    def request(self, req, state, icon):
        ret = None
        err = None
        for host in self.host:
            #req = urllib.parse.quote(req)
            url = f'http://nas.wg/api/lights.php?host={host}&{req}'
            try:
                with urllib.request.urlopen(url) as response:
                    res = json.loads(response.read())
                    try:
                        if res["result"]["success"] == True:
                            self.state = state
                            ret = icon
                            #return icon
                        else:
                            err = json.dumps(res)
                            #return json.dumps(res)
                    except:
                        if ret == None:
                            err = json.dumps(res)
                        #return json.dumps(res)
            except:
                pass
        if ret != None:
            return ret
        if err == None:
            raise Exception("No lights online")
        return err

    def run(self, context):
        bot = context.bot
        try:
            res = self.request('state=true')
            bot.send_message(chat_id=self.chat_id, text=res)
        except:
            text = traceback.format_exc(1)
            bot.send_message(chat_id=self.chat_id, text=text)

    def cmd(self, update, context):
        bot = context.bot
        if update.effective_chat.id != self.chat_id:
            bot.send_message(chat_id=update.effective_chat.id, text="403")
            return

        try:
            query = update.message.text
            seg = query.split()[1:]
            req = 'state=true'
            icon = '💡'

            if len(seg) < 1:
                seg = ['on' if self.state == 'off' else 'off']

            if seg[0] == 'off':
                icon = '🌑'
                req = 'state=false'
            elif seg[0] == 'on':
                req = 'state=true'
            elif seg[0] in {'warm', 'daylight', 'cool', 'night'}:
                if seg[0] in {'warm', 'night'}:
                    icon = '🌕'
                req = f'scene={seg[0]}'
            else:
                req = seg[0]

            text = self.request(req, seg[0], icon)
            if not text:
                text = 'empty'
            msg = bot.send_message(chat_id=update.effective_chat.id, text=text)
            #query = update.message.text
            #host = query.split(maxsplit = 1)[1]
            #online = self.ping(host)
            #text = self.oltext(host, online)
            #context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN)
            self.delete_msgs()
            self.msgs.append(update.message)
            self.msgs.append(msg)
        except:
            text = traceback.format_exc(1)
            bot.send_message(chat_id=update.effective_chat.id, text=text)

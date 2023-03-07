#!/usr/bin/env python3
import json, traceback
import urllib.parse, urllib.request
from telegram.ext import CommandHandler

__all__ = ["register"]

def register(app):
    app.add_handler(CommandHandler('python3', tgbot_python3))
    app.add_handler(CommandHandler('py', tgbot_python3))
    app.add_handler(CommandHandler('run', tgbot_run))

def run(lan, src):
    src = urllib.parse.quote(src)
    with urllib.request.urlopen(f'http://api.paiza.io/runners/create?source_code={src}&language={lan}&longpoll=true&longpoll_timeout=10&api_key=guest', data=b'') as response:
        res = json.loads(response.read())
        result = json.dumps(res)
        if "error" in res:
            return result
        if res["status"] != 'completed':
            return result
        rid = res["id"]
        with urllib.request.urlopen(f'http://api.paiza.io:80/runners/get_details?id={rid}&api_key=guest') as response:
            res = json.loads(response.read())
            result = json.dumps(res)
            if res["result"] in ["success", "failure"]:
                time = res["time"]
                rc = res["exit_code"]
                sout = res["stdout"].strip()
                serr = res["stderr"].strip()
                out = []
                if time != "0.00":
                    out += [f'⏱ {time}']
                if rc != 0:
                    out += [f'💥 {rc}']
                if sout:
                    out += [sout]
                if serr:
                    out += ['❌', serr]
                result = '\n'.join(out)
    return result

def run_python3(src):
    return run('python3', src)

async def tgbot_run(update, context):
    try:
        query = update.message.text
        query = query.split(maxsplit = 1)[1]
        lan, query = query.split(maxsplit = 1)
        text = run(lan, query)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    except:
        text = traceback.format_exc(0)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def tgbot_python3(update, context):
    try:
        query = update.message.text
        query = query.split(maxsplit = 1)[1]
        text = run_python3(query)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    except:
        text = traceback.format_exc(0)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

from telegram.ext import CommandHandler
import wolframalpha
import traceback
from config import wfa_app_id, chat_id_admin

__all__ = ['register']

# WolframAlpha
wfa_client = wolframalpha.Client(wfa_app_id)

def wfa_format_all(res):
    if res.success != True:
        return "Sorry, I don't understand that"
    text = ''
    for pod in res.pods:
        podtext = ''
        for sub in pod.subpods:
            if sub.plaintext:
                podtext += '\n' + sub.plaintext
        if podtext:
            text += ('\n' if text else '') + '💡 ' + pod.title + podtext
    return text

async def wfa(update, context):
    query = update.message.text
    query = query.split(' ')[1:]
    query = ' '.join(query)
    if not query:
        text = "Maybe I am a calculator, ask me something?"
    else:
        try:
            global wfa_client
            res = wfa_client.query(query)
            text = wfa_format_all(res)
        except:
            text = "What happened, something went wrong"
            report = "What happened?\n" + query + "\n" + traceback.format_exc()
            await context.bot.send_message(chat_id=chat_id_admin, text=report)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def register(app):
    app.add_handler(CommandHandler('wfa', wfa))

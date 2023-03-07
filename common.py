#!/usr/bin/env python3
from telegram.ext import CallbackContext

__all__ = ["job_send_msg", "job_del_msg"]

async def cb_job_send_msg(context: CallbackContext):
    await context.bot.send_message(**context.job.data)

def job_send_msg(app, chat_id, text):
    app.job_queue.run_once(cb_job_send_msg, 0, name=job_send_msg.__name__, data={"text":text, "chat_id":chat_id})


async def cb_job_del_msg(context: CallbackContext):
    for m in context.job.data:
        await m.delete()

def job_del_msg(app, delay, msgs):
    app.job_queue.run_once(cb_job_del_msg, delay, name=job_del_msg.__name__, data=msgs)

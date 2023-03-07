from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackContext
from telegram import helpers
from datetime import datetime, timedelta, timezone
import services
from common import *

__all__ = ['register']

service = services.Service('alive')

class AliveBot:
	# Message auto delete timer
	auto_delete_sec = 3
	# Interval between check in
	interval = 24 * 60 * 60
	#interval = 10
	# Extra delay to wait for response before sending out each public broadcast
	public_wait = interval / 2
	# Start sending out public broadcasts after this time (multiples of interval) has elapsed
	public_interval = interval * 2
	# No more public broadcasts after this time
	public_interval_max = public_interval + interval * 7 + public_wait

	def __init__(self, app):
		self.app = app
		self.clients = {}
		for c in service:
			if 'public' in c:
				self.new_client(int(c.name))
		app.add_handler(CommandHandler('alive', self.message))

	def new_client(self, chat_id):
		if chat_id in self.clients:
			return
		self.clients[chat_id] = {'client_msgs':[], 'public_msgs':[]}
		self.app.job_queue.run_once(self.check_client_job, timedelta(seconds=0), chat_id)

	async def check_client(self, chat_id):
		utcnow = datetime.now(timezone.utc)
		client = service[chat_id]
		if 'public' not in client:
			return
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()
		next = self.interval - sec if sec < self.interval else self.interval
		self.app.job_queue.run_once(self.check_client_job, timedelta(seconds=next), chat_id)

		if sec >= self.public_interval_max:
			return

		if sec >= self.interval:
			sdelta = timedelta(seconds=round(sec))
			text = f"_Beep\\-boop\\!_\nLast checked in *{helpers.escape_markdown(str(sdelta), 2)}* ago\\.\nCheck in? \\/alive"
			msg = await self.app.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN_V2, text=text)
			await self.delete_msgs(self.clients[chat_id]['client_msgs'])
			self.clients[chat_id]['client_msgs'] = [msg]

		if sec >= self.public_interval:
			self.app.job_queue.run_once(self.public_job, timedelta(seconds=self.public_wait), chat_id)

	async def check_client_job(self, context: CallbackContext):
		self.check_client(context.job.data)

	async def public_job(self, context: CallbackContext):
		utcnow = datetime.now(timezone.utc)
		chat_id = context.job.data
		client = service[chat_id]
		if 'public' not in client:
			return
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()
		if sec < self.public_interval:
			return

		msg = await self.public_broadcast(chat_id, int(client['public']))
		await self.delete_msgs(self.clients[chat_id]['public_msgs'])
		self.clients[chat_id]['public_msgs'] = [msg]

	async def public_broadcast(self, chat_id, dst_id):
		utcnow = datetime.now(timezone.utc)
		client = service[chat_id]
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()

		chat = await self.app.bot.get_chat(chat_id)
		sdelta = timedelta(seconds=round(sec))
		custom = client['custom']
		text = f"""
_Beep\\-boop\\!_
{helpers.escape_markdown(f"{chat.first_name} {chat.last_name} @{chat.username}", 2)}
Last seen *{helpers.escape_markdown(str(sdelta), 2)}* ago\\.

{custom.decode('utf8') if custom else ''}
""".strip()
		return await self.app.bot.send_message(chat_id=dst_id, parse_mode=ParseMode.MARKDOWN_V2, text=text)


	async def delete(self, msg):
		try:
			await msg.delete()
		except:
			pass

	async def delete_msgs(self, msgs):
		for m in msgs:
			await self.delete(m)

	async def delete_chat_msgs(self, chat_id):
		await self.delete_msgs(self.clients[chat_id]['public_msgs'])
		self.clients[chat_id]['public_msgs'] = []
		await self.delete_msgs(self.clients[chat_id]['client_msgs'])
		self.clients[chat_id]['client_msgs'] = []

	async def message(self, update, context):
		chat_id = update.effective_chat.id
		client = service[chat_id]
		client['timestamp'] = datetime.now(timezone.utc).timestamp()
		if chat_id in self.clients:
			await self.delete_chat_msgs(chat_id)

		query = update.message.text_markdown_v2
		query = query.split(maxsplit=1)[1:]
		if not query:
			msg = await context.bot.send_message(chat_id=chat_id,
				parse_mode=ParseMode.MARKDOWN_V2, text="_Beep\\-boop\\!_")

			job_del_msg(self.app, timedelta(seconds=self.auto_delete_sec),
				[update.message, msg])
			return
		try:
			text = '?'
			query = query[0].split(maxsplit=1)
			action = query[0]
			if action == 'register':
				public_chat_id = int(query[1].replace('\\', ''))
				client['public'] = public_chat_id
				self.new_client(chat_id)
				text = helpers.escape_markdown(f"""
Register successful: {public_chat_id}
See you again in {round(timedelta(seconds=self.interval).total_seconds()/60.0/60.0)} hours!
""", 2)
			elif action == 'cancel':
				del client['public']
				text = helpers.escape_markdown(f"Unregistered.", 2)
			elif action == 'custom':
				if len(query) < 2:
					del client['custom']
				else:
					client['custom'] = query[1]
				return await self.public_broadcast(chat_id, chat_id)
			elif action == 'test':
				return await self.public_broadcast(chat_id, chat_id)
			else:
				raise Exception("help")
		except:
			return await self.help(update, context)
		await context.bot.send_message(chat_id=chat_id,
			parse_mode=ParseMode.MARKDOWN_V2, text=text)

	async def help(self, update, context):
		await context.bot.send_message(
			chat_id=update.effective_chat.id,
			parse_mode=ParseMode.MARKDOWN_V2,
			text=f"""
_Beep\\-boop\\!_ Alive monitor\\.
This bot will send a check in message to you every *{round(timedelta(seconds=self.interval).total_seconds()/60.0/60.0)} hours*\\.
After *{round(timedelta(seconds=self.public_interval+self.public_wait).total_seconds()/60.0/60.0)} hours*, a broadcast message will be send out to specified public chat\\.

Commands:
`/alive register <chat_id>`
Register check in monitoring for you, send public broadcast to `<chat_id>`
`/alive cancel`
Cancel check in monitoring
`/alive`
Check in now
`/alive test`
Test public broadcast message in private chat
`/alive custom <message\\.\\.\\.>`
Append `<message...>` to public broadcast message
""".strip())

def register(app):
	AliveBot(app)

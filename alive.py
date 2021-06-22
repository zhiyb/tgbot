from telegram import ParseMode
from telegram.ext import CommandHandler
from telegram.utils import helpers
from datetime import datetime, timedelta, timezone
import services

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

	def __init__(self, updater):
		self.updater = updater
		self.clients = {}
		for c in service:
			if 'public' in service[c]:
				self.new_client(int(c))
		updater.dispatcher.add_handler(CommandHandler('alive', self.message))

	def new_client(self, chat_id):
		if chat_id in self.clients:
			return
		self.clients[chat_id] = {'client_msgs':[], 'public_msgs':[]}
		self.updater.job_queue.run_once(self.check_client_job, timedelta(seconds=0), chat_id)

	def check_client(self, chat_id):
		utcnow = datetime.now(timezone.utc)
		client = service[chat_id]
		if 'public' not in client:
			return
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()
		next = self.interval - sec if sec < self.interval else self.interval
		self.updater.job_queue.run_once(self.check_client_job, timedelta(seconds=next), chat_id)

		if sec >= self.public_interval_max:
			return

		if sec >= self.interval:
			sdelta = timedelta(seconds=round(sec))
			text = f"_Beep\\-boop\\!_\nLast checked in *{helpers.escape_markdown(str(sdelta), 2)}* ago\\.\nCheck in? \\/alive"
			msg = self.updater.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN_V2, text=text)
			for m in self.clients[chat_id]['client_msgs']:
				self.delete(m)
			self.clients[chat_id]['client_msgs'] = [msg]

		if sec >= self.public_interval:
			self.updater.job_queue.run_once(self.public_job, timedelta(seconds=self.public_wait), chat_id)

	def check_client_job(self, context):
		self.check_client(context.job.context)

	def public_job(self, context):
		utcnow = datetime.now(timezone.utc)
		chat_id = context.job.context
		client = service[chat_id]
		if 'public' not in client:
			return
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()
		if sec < self.public_interval:
			return

		msg = self.public_broadcast(chat_id, int(client['public']))
		for m in self.clients[chat_id]['public_msgs']:
			self.delete(m)
		self.clients[chat_id]['public_msgs'] = [msg]

	def public_broadcast(self, chat_id, dst_id):
		utcnow = datetime.now(timezone.utc)
		client = service[chat_id]
		time = datetime.fromtimestamp(float(client['timestamp']), timezone.utc)
		delta = utcnow - time
		sec = delta.total_seconds()

		chat = self.updater.bot.get_chat(chat_id)
		sdelta = timedelta(seconds=round(sec))
		custom = client['custom']
		text = f"""
_Beep\\-boop\\!_
{helpers.escape_markdown(f"{chat.first_name} {chat.last_name} @{chat.username}", 2)}
Last seen *{helpers.escape_markdown(str(sdelta), 2)}* ago\\.

{custom.decode('utf8') if custom else ''}
""".strip()
		return self.updater.bot.send_message(chat_id=dst_id, parse_mode=ParseMode.MARKDOWN_V2, text=text)


	def delete(self, msg):
		try:
			msg.delete()
		except:
			pass

	def delete_msgs(self, chat_id):
		for m in self.clients[chat_id]['public_msgs']:
			self.delete(m)
		self.clients[chat_id]['public_msgs'] = []
		for m in self.clients[chat_id]['client_msgs']:
			self.delete(m)
		self.clients[chat_id]['client_msgs'] = []

	def message(self, update, context):
		chat_id = update.effective_chat.id
		client = service[chat_id]
		client['timestamp'] = datetime.now(timezone.utc).timestamp()
		if chat_id in self.clients:
			self.delete_msgs(chat_id)

		query = update.message.text_markdown_v2
		query = query.split(maxsplit=1)[1:]
		if not query:
			msg = context.bot.send_message(chat_id=chat_id,
				parse_mode=ParseMode.MARKDOWN_V2, text="_Beep\\-boop\\!_")

			def delete_messages(context):
				for m in context.job.context:
					self.delete(m)
			self.updater.job_queue.run_once(delete_messages, timedelta(seconds=self.auto_delete_sec),
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
				return self.public_broadcast(chat_id, chat_id)
			elif action == 'test':
				return self.public_broadcast(chat_id, chat_id)
			else:
				raise Exception("help")
		except:
			return self.help(update, context)
		context.bot.send_message(chat_id=chat_id,
			parse_mode=ParseMode.MARKDOWN_V2, text=text)

	def help(self, update, context):
		context.bot.send_message(
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

def register(updater):
	AliveBot(updater)

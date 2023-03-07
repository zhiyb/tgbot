from datetime import timedelta
import hashlib, base64
from cryptography.fernet import Fernet
from telegram.constants import ParseMode
from telegram.ext import CommandHandler
import services
from common import *

__all__ = ['register']

service = services.Service('vault')

class Vault:
	def __init__(self, client_name):
		self.client = service[client_name]

	def __getitem__(self, key):
		key = key.encode('utf8')
		m = hashlib.sha256()
		m.update(key)
		enc_key = base64.b64encode(m.digest())
		m.update(key)
		cli_key = base64.b64encode(m.digest())
		cipher = Fernet(enc_key)
		del enc_key
		data = self.client[cli_key]
		if data == None:
			return None
		data = cipher.decrypt(bytes(data))
		del cipher
		return data.decode('utf8')

	def __setitem__(self, key, data):
		key = key.encode('utf8')
		m = hashlib.sha256()
		m.update(key)
		enc_key = base64.b64encode(m.digest())
		m.update(key)
		cli_key = base64.b64encode(m.digest())
		cipher = Fernet(enc_key)
		del enc_key
		enc = cipher.encrypt(data.encode('utf8'))
		del cipher
		self.client[cli_key] = enc

	def __delitem__(self, key):
		key = key.encode('utf8')
		m = hashlib.sha256()
		m.update(key)
		#enc_key = base64.b64encode(m.digest())
		m.update(key)
		cli_key = base64.b64encode(m.digest())
		del self.client[cli_key]

	def destroy(self):
		del service[self.client]

class VaultBot:
	auto_delete_sec = 60

	def __init__(self, app):
		self.app = app
		app.add_handler(CommandHandler('vault', self.message))

	async def message(self, update, context):
		query = update.message.text_markdown_v2
		query = query.split(maxsplit=2)[1:]
		action = 'help'
		if len(query) >= 1:
			action = query[0]
		if action in {'add', 'get', 'set', 'del'}:
			if len(query) >= 2:
				data = query[1]
			else:
				action = 'help'
		else:
			action = 'help'
		if action == 'help':
			text = f"""
Bot's vault stores text encrypted\\.
Commands and replies will be automatically deleted after {self.auto_delete_sec} seconds\\.

Commands:
`/vault set <key> (newline) <text>`
Replace content of vault associated with `<key>` with `<text>`
`/vault add <key> (newline) <text>`
Append `<text>` to the end of vault associated with `<key>`
`/vault del <key>`
Delete vault associated with `<key>`
`/vault get <key>`
Retrieve content of vault associated with `<key>`
""".strip()
			await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode=ParseMode.MARKDOWN_V2, text=text)
			return

		data = data.split('\n', maxsplit=1)
		key = f"{update.effective_chat.id}_{data[0]}"
		data = data[1] if len(data) >= 2 else None
		vault = Vault(str(update.effective_chat.id))

		if action == 'set':
			if data == None:
				del vault[key]
			else:
				vault[key] = data
		elif action == 'add':
			if data != None:
				text = vault[key]
				if text == None:
					vault[key] = data
				else:
					vault[key] = f"{text}\n{data}"
		elif action == 'del':
			del vault[key]

		# Return new data
		text = vault[key]
		del key
		if text == None:
			text = 'No record'
		else:
			text = 'Record found:\n' + text
		msgs = await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode=ParseMode.MARKDOWN_V2, text=text)
		msgs = [update.message, msgs]

		job_del_msg(self.app, timedelta(seconds=self.auto_delete_sec), msgs)

def register(app):
	VaultBot(app)

def main():
	services.nocommit()

	vault1 = Vault('user_id_1')
	vault1['test1'] = 'content_1'
	vault1['test2'] = 'content_2'

	if vault1['test1'] != 'content_1':
		raise Exception(f"Wrong value: {vault1['test1']}")
	if vault1['test2'] != 'content_2':
		raise Exception(f"Wrong value: {vault1['test2']}")

	vault1.destroy()

	print("all ok")
	return 0

if __name__ == '__main__':
	main()

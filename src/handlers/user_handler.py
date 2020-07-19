from typing import List

import translations
import strings
from client import Client, ChatMode

def handle_email(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.EMAIL)
		return
	c.set_email(args[0])
	c.send(strings.USER.UPDATED_EMAIL)

def handle_exit(c: Client, args: List[str]) -> None:
	c.quit()

def handle_language(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		for lang in translations.languages.keys():
			c.send(lang)
	elif len(args) == 1:
		if args[0] != "client" and not args[0] in translations.languages:
			c.send(strings.USER.NO_LANGUAGE, lang=args[0])
		else:
			c.set_language(args[0])
			c.send(strings.USER.UPDATED_LANGUAGE)
	else:
		c.send(strings.USAGE.LANGUAGE)

def handle_passwd(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.PASSWD)
		return
	c.set_password(" ".join(args))
	c.send(strings.USER.UPDATED_PASSWORD)

def handle_redeem(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.REDEEM)
	elif c.premium:
		c.send(strings.USER.ALREADY_PREMIUM)
	elif c.redeem_code(args[0]):
		c.send(strings.USER.REDEEM_SUCCESS)
	else:
		c.send(strings.USER.REDEEM_FAIL)

def handle_username(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.USERNAME)
	elif not c.checkvalid(args[0]):
		c.send(strings.USER.ALPHANUM_USERNAME)
	elif c.set_username(args[0]):
		c.send(strings.USER.UPDATED_USERNAME)
	else:
		c.send(strings.USER.USERNAME_TAKEN, username=args[0])

def handle_chat(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.CHAT)
		return
	try:
		mode = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	chat_mode = None
	if mode == 0:
		chat_mode = ChatMode.OFF
	elif mode == 1:
		chat_mode = ChatMode.DIRECT
	elif mode == 2:
		chat_mode = ChatMode.LOCAL
	elif mode == 3:
		chat_mode = ChatMode.GLOBAL
	else:
		c.send(strings.USER.INVALID_CHAT)
		return
	c.set_chat(chat_mode)
	c.send(strings.USER.SET_CHAT)


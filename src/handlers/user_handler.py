from typing import List
import random

import quest
import translations
import strings
import crafting
import config
import database
import production
from client import Client, ChatMode
from cargo import Cargo

conn = database.conn

CRATE_MAX_OUTFIT = config.get_section("crafting").getint("CrateMaxOutfit")

def handle_email(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.EMAIL, error=True)
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
			c.send(strings.USER.NO_LANGUAGE, lang=args[0], error=True)
		else:
			c.set_language(args[0])
			c.send(strings.USER.UPDATED_LANGUAGE)
	else:
		c.send(strings.USAGE.LANGUAGE)

def handle_passwd(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.PASSWD, error=True)
		return
	c.set_password(" ".join(args))
	c.send(strings.USER.UPDATED_PASSWORD)

def handle_redeem(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.REDEEM, error=True)
	elif c.premium:
		c.send(strings.USER.ALREADY_PREMIUM, error=True)
	elif c.redeem_code(args[0]):
		c.send(strings.USER.REDEEM_SUCCESS)
	else:
		c.send(strings.USER.REDEEM_FAIL, error=True)

def handle_username(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.USERNAME, error=True)
	elif not c.checkvalid(args[0]):
		c.send(strings.USER.ALPHANUM_USERNAME, error=True)
	elif c.set_username(args[0]):
		c.send(strings.USER.UPDATED_USERNAME)
	else:
		c.send(strings.USER.USERNAME_TAKEN, username=args[0], error=True)

def handle_chat(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.CHAT, error=True)
		return
	try:
		mode = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
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
		c.send(strings.USER.INVALID_CHAT, error=True)
		return
	c.set_chat(chat_mode)
	c.send(strings.USER.SET_CHAT)

def handle_crate(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send(strings.USAGE.CRATE, error=True)
		return
	try:
		cindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	if cindex >= len(c.structure.cargo):
		c.send(strings.MISC.NO_CARGO, error=True)
		return
	cargo = c.structure.cargo[cindex]
	if cargo.type != "Crate":
		c.send(strings.USER.NOT_CRATE, error=True)
		return
	elif cargo.count < count:
		c.send(strings.CRAFT.INSUFFICIENTS)
		return
	cargo.extra = int(cargo.extra)
	for i in range(count):
		if cargo.theme != None:
			outfit = random.choice(outfittype.outfits.values())
			Cargo(outfit.name, 1, cargo.extra, cargo.theme).add(c.structure)
			c.send(strings.USER.CRATE_EXTRA, name=util.theme_str(outfit.name, cargo.theme), extra=cargo.extra)
			continue
		recipe = random.choice(crafting.recipes)
		if recipe.has_extra:
			extra = min(random.randint(cargo.extra / 2, cargo.extra), CRATE_MAX_OUTFIT)
			Cargo(recipe.output, 1, extra).add(c.structure)
			c.send(strings.USER.CRATE_EXTRA, name=recipe.output, extra=extra)
		else:
			ccount = random.randint(cargo.extra / 2, cargo.extra)
			Cargo(recipe.output, ccount, None).add(c.structure)
			c.send(strings.USER.CRATE, name=recipe.output, count=ccount)
	cargo.less(count, c.structure)

def handle_quest(c: Client, args: List[str]) -> None:
	report = production.update(c.structure)
	for q in quest.get_quests(c.id):
		if q.is_done(c.structure, report):
			q.remove(c.id)
			c.send(strings.USER.QUEST_COMPLETED, name=c.translate(q.name))
			if q.next != None:
				q.next.add(c.id)
				c.send(strings.USER.QUEST_ADDED, name=c.translate(q.next.name))
	conn.commit()
	for q in quest.get_quests(c.id):
		c.send(strings.USER.QUEST, name=c.translate(q.name), desc=c.translate(q.desc))


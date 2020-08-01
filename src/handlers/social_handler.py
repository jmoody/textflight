import logging
import re
from typing import List

import network
import structure
import strings
from client import Client, MessageType, ChatMode

validchars = re.compile(r"[^ -~]+")	# Only allow printable ASCII

format_codes = {
	"^0": "\033[0m",
	"^1": "\033[31m",
	"^2": "\033[32m",
	"^3": "\033[33m",
	"^4": "\033[34m",
	"^5": "\033[36m",
	"^6": "\033[95m",
	"^7": "\033[37m",
	"^8": "\033[30m",
}

def apply_format_codes(message: str) -> None:
	for code, value in format_codes.items():
		message = message.replace(code, value)
	message+= "\033[0m"
	return message

def handle_fact(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.FACT)
		return
	elif c.faction_id == 0:
		c.send(strings.MISC.NOT_IN_FACTION)
		return
	message = validchars.sub("", " ".join(args))
	if c.premium:
		message = apply_format_codes(message)
	for client in network.clients:
		if client.id != None and client.chat_mode.value >= ChatMode.LOCAL.value and client.faction_id == c.faction_id:
			client.chat(MessageType.FACTION, c.username, message)
	logging.info("Faction message '%s' sent by %d.", message, c.id)
	c.send(strings.SOCIAL.FACTION)

def handle_glob(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.GLOB)
		return
	message = validchars.sub("", " ".join(args))
	if c.premium:
		message = apply_format_codes(message)
	for client in network.clients:
		if client.id != None and client.chat_mode.value >= ChatMode.GLOBAL.value:
			client.chat(MessageType.GLOBAL, c.username, message)
	logging.info("Global message '%s' sent by %d.", message, c.id)
	c.send(strings.SOCIAL.GLOBAL)

def handle_subs(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send(strings.USAGE.SUBS)
		return
	username = args.pop(0)
	for client in network.clients:
		if client.id != None and client.username == username:
			if client.chat_mode.value < ChatMode.DIRECT.value:
				c.send(strings.SOCIAL.NO_CHAT)
				return
			message = validchars.sub("", " ".join(args))
			if c.premium:
				message = apply_format_codes(message)
			client.chat(MessageType.SUBSPACE, c.username, message)
			logging.info("Subspace message '%s' sent by %d, to %d.", message, c.id, client.id)
			c.send(strings.SOCIAL.SUBSPACE)
			return
	c.send(strings.MISC.NO_OP)

def handle_locl(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.LOCL)
		return
	name = "%d %s" % (c.structure.id, c.structure.name)
	message = validchars.sub("", " ".join(args))
	if c.premium:
		message = apply_format_codes(message)
	for client in network.clients:
		if client.id != None and client.chat_mode.value >= ChatMode.LOCAL.value and client.structure.system.id == c.structure.system.id:
			client.chat(MessageType.LOCAL, name, message)
	logging.info("Local message '%s' sent by %d.", message, c.id)
	c.send(strings.SOCIAL.LOCAL)

def handle_hail(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send(strings.USAGE.HAIL)
		return
	try:
		sid = int(args.pop(0))
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	for client in network.clients:
		if client.id != None and client.structure.id == sid:
			if client.structure.system.id != c.structure.system.id:
				c.send(strings.MISC.NO_STRUCT)
				return
			elif client.chat_mode.value < ChatMode.DIRECT.value:
				c.send(strings.SOCIAL.NO_CHAT)
				return
			message = validchars.sub("", " ".join(args))
			if c.premium:
				message = apply_format_codes(message)
			client.chat(MessageType.HAIL, "%d %s" % (c.structure.id, c.structure.name), message)
			logging.info("Hail message '%s' sent by %d, to %d.", message, c.id, client.id)
			c.send(strings.SOCIAL.HAIL, id=sid, name=client.structure.name)
			return
	c.send(strings.SOCIAL.NO_HAIL)


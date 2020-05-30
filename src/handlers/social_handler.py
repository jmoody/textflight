import logging
import re
from typing import List

import network
import structure
from client import Client, MessageType

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
		c.send("Usage: fact <message>")
		return
	elif c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	message = validchars.sub("", " ".join(args))
	if c.premium:
		message = apply_format_codes(message)
	for client in network.clients:
		if client.chat_on and client.faction_id == c.faction_id:
			client.chat(MessageType.FACTION, c.username, message)
	logging.info("Faction message '%s' sent by %d.", message, c.id)
	c.send("Broadcast message to faction.")

def handle_subs(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send("Usage: subs <username> <message>")
		return
	username = args.pop(0)
	for client in network.clients:
		if client.username == username:
			if not client.chat_on:
				c.send("Operator has chat disabled.")
				return
			message = validchars.sub("", " ".join(args))
			if c.premium:
				message = apply_format_codes(message)
			client.chat(MessageType.SUBSPACE, c.username, message)
			logging.info("Subspace message '%s' sent by %d, to %d.", message, c.id, client.id)
			c.send("Sent message via subspace link.")
			return
	c.send("Unable to locate operator.")

def handle_locl(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send("Usage: locl <message>")
		return
	name = "%d %s" % (c.structure.id, c.structure.name)
	message = validchars.sub("", " ".join(args))
	if c.premium:
		message = apply_format_codes(message)
	for client in network.clients:
		if client.chat_on and client.structure.system.id == c.structure.system.id:
			client.chat(MessageType.LOCAL, name, message)
	logging.info("Local message '%s' sent by %d.", message, c.id)
	c.send("Broadcast message to local system.")

def handle_hail(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send("Usage: hail <structure ID> <message>")
		return
	try:
		sid = int(args.pop(0))
	except ValueError:
		c.send("Not a number.")
		return
	for client in network.clients:
		if client.structure.id == sid:
			if client.structure.system.id != c.structure.system.id:
				break
			elif not client.chat_on:
				c.send("Operator has chat disabled.")
			message = validchars.sub("", " ".join(args))
			if c.premium:
				message = apply_format_codes(message)
			client.chat(MessageType.HAIL, "%d %s" % (c.structure.id, c.structure.name), message)
			logging.info("Hail message '%s' sent by %d, to %d.", message, c.id, client.id)
			c.send("Sent hail to '%d %s'.", (sid, client.structure.name))
			return
	c.send("Unable to hail structure.")


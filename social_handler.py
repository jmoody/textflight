from typing import List

import network
import structure
from client import Client, MessageType

def handle_fact(c: Client, args: List[str]) -> None:
	pass

def handle_subs(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send("Usage: subs <username> <message>")
		return
	username = args.pop(0)
	for client in network.clients:
		if client.username == username:
			client.chat(MessageType.SUBSPACE, c.username, " ".join(args))
			c.send("Sent message via subspace link.")
			return
	c.send("Unable to locate user.")

def handle_locl(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send("Usage: locl <message>")
		return
	for client in network.clients:
		if client.structure.system.id == c.structure.system.id:
			client.chat(MessageType.LOCAL, "%d %s" % (c.structure.id, c.structure.name), " ".join(args))
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
			client.chat(MessageType.HAIL, "%d %s" % (c.structure.id, c.structure.name), " ".join(args))
			c.send("Sent hail to '%d %s'.", (sid, client.structure.name))
			return
	c.send("Unable to hail structure.")


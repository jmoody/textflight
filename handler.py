from typing import List

import database
import client
import system
import info_handler
import struct_handler
import ship_handler
from client import Client

COMMANDS = {
	"board": "Board another structure.",
	"dock": "Dock to a nearby structure.",
	"eject": "Disconnects all docked structures.",
	"exit": "Disconnects from server.",
	"help": "Shows list of commands, or usage of a given command.",
	"install": "Install an outfit from cargo.",
	"jump": "Jump to another system.",
	"land": "Land on a planet.",
	"language": "Set your language.",
	"launch": "Launch from planets or docked structures.",
	"load": "Load cargo onto another structure.",
	"nav": "Get navigation information such as planets and hyperlinks.",
	"rename": "Rename structure.",
	"scan": "Scan nearby structures for outfits and cargo.",
	"set": "Change the power setting of installed outfits.",
	"status": "Show status of local structure.",
	"uninstall": "Uninstall an outfit into cargo.",
}

HELP_MESSAGE = "No such command '%s'. Use 'help' for a list of commands."

def handle_command(c: Client, cmd: str, args: List[str]) -> None:
	if cmd == "exit":
		c.quit()
		return
	elif cmd == "help":
		handle_help(c, args)
	elif cmd == "install":
		struct_handler.handle_install(c, args)
	elif cmd == "jump":
		ship_handler.handle_jump(c, args)
	elif cmd == "nav":
		info_handler.handle_nav(c)
	elif cmd == "rename":
		info_handler.handle_rename(c, args)
	elif cmd == "scan":
		info_handler.handle_scan(c, args)
	elif cmd == "set":
		struct_handler.handle_set(c, args)
	elif cmd == "status":
		info_handler.handle_status(c)
	elif cmd == "uninstall":
		struct_handler.handle_uninstall(c, args)
	else:
		c.send(HELP_MESSAGE, (cmd,))
	c.prompt()

def handle_help(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		for k, v in COMMANDS.items():
			c.send("%s: %s", (k, c.translate(v)))
	else:
		cmd = args[0]
		if not cmd in COMMANDS:
			c.send("No such command '%s'", (cmd,))
		else:
			c.send("%s: %s", (cmd, c.translate(COMMANDS[cmd])))

def handle_login(c: Client, cmd: str, args: List[str]) -> None:
	if cmd == "login":
		if len(args) != 2:
			c.send("Usage: login <username> <password>.")
		elif c.login(args[0], args[1]):	# TODO: Hash password, don't store cleartext
			c.send("Logged in as %s.", (args[0],))
		else:
			c.send("Incorrect username or password.")
	elif cmd == "register":
		if len(args) != 2:
			c.send("Usage: register <username> <password>. Username and password cannot contain spaces.")
			c.prompt()
			return
		if database.get_user_by_username(args[0]) != None:
			c.send("Username '%s' is already taken.", (args[0],))
		else:
			client.register_user(args[0], args[1])
			c.send("Registration successful! Try logging in with 'login [username] [password]'.")
	elif cmd == "exit":
		c.quitting = True
		return
	else:
		c.send("You are not logged in; use 'login [username] [password]' to log in, or 'register [username] [password]' to create a new account.")
	c.prompt()


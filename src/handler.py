from typing import List

import database
import client
import system
import combat_handler
import craft_handler
import faction_handler
import info_handler
import ship_handler
import social_handler
import struct_handler
import network
from client import Client

HELP_MESSAGE = "No such command '%s'. Use 'help' for a list of commands."

def handle_email(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: email <new email>")
		return
	c.set_email(args[0])
	c.send("Updated email address.")

def handle_exit(c: Client, args: List[str]) -> None:
	c.quit()

def handle_passwd(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send("Usage: passwd <new password>")
		return
	c.set_password(" ".join(args))
	c.send("Updated password.")

def handle_username(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: username <new username>")
	elif not c.checkvalid(args[0]):
		c.send("Username can only contain letters and numbers.")
	elif c.set_username(args[0]):
		c.send("Updated username.")
	else:
		c.send("Username '%s' is already taken.", (args[0],))

def handle_chat(c: Client, args: List[str]) -> None:
	c.set_chat(not c.chat_on)
	if c.chat_on:
		c.send("Enabled chat.")
	else:
		c.send("Disabled chat.")

def handle_help(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		for k, v in COMMANDS.items():
			c.send("%s: %s", (k, c.translate(v[0])))
	else:
		cmd = args[0]
		if not cmd in COMMANDS:
			c.send("No such command '%s'", (cmd,))
		else:
			c.send("%s: %s", (cmd, c.translate(COMMANDS[cmd][0])))

COMMANDS = {
	"airlock": ("Remove someone from your structure.", struct_handler.handle_airlock),
	"base": ("Construct a planetary base.", craft_handler.handle_base),
	"board": ("Board another structure.", struct_handler.handle_board),
	"cancel": ("Cancel a queued assembly. Yields no resources.", craft_handler.handle_cancel),
	"capture": ("Capture a nearby structure.", combat_handler.handle_capture),
	"chat": ("Toggles chat on or off.", handle_chat),
	"construct": ("Construct a new structure.", craft_handler.handle_construct),
	"craft": ("Queue an item for assembly.", craft_handler.handle_craft),
	"destroy": ("Destroy a nearby structure.", combat_handler.handle_destroy),
	"dock": ("Dock to a nearby structure.", ship_handler.handle_dock),
	"eject": ("Disconnect docked structures.", struct_handler.handle_eject),
	"email": ("Set your email address.", handle_email),
	"exit": ("Disconnect from server.", handle_exit),
	"fact": ("Broadcast a message to your faction.", social_handler.handle_fact),
	"faction_chown": ("Change faction owner.", faction_handler.handle_chown),
	"faction_claim": ("Claim a system or planet for your faction.", faction_handler.handle_claim),
	"faction_info": ("Display faction info.", faction_handler.handle_info),
	"faction_join": ("Join a faction.", faction_handler.handle_join),
	"faction_kick": ("Kick an operator from your faction.", faction_handler.handle_kick),
	"faction_leave": ("Leave a faction.", faction_handler.handle_leave),
	"faction_list": ("List all factions.", faction_handler.handle_list),
	"faction_name": ("Name a claimed system or planet.", faction_handler.handle_name),
	"faction_passwd": ("Change your faction password.", faction_handler.handle_passwd),
	"faction_release": ("Releas your faction's claim on a system or planet.", faction_handler.handle_release),
	"faction_rename": ("Rename your faction.", faction_handler.handle_rename),
	"faction_rep": ("View or set operator reputations.", faction_handler.handle_frep),
	"faction_repf": ("View or set faction reputations.", faction_handler.handle_frepf),
	"hail": ("Hail a structure.", social_handler.handle_hail),
	"help": ("Show list of commands, or usage of a given command.", handle_help),
	"install": ("Install an outfit from cargo.", struct_handler.handle_install),
	"jettison": ("Discard cargo into space.", craft_handler.handle_jettison),
	"jump": ("Jump to another system.", ship_handler.handle_jump),
	"land": ("Land on a planet.", ship_handler.handle_land),
	"language": ("Set your language.", None),
	"launch": ("Launch off a planet.", ship_handler.handle_launch),
	"load": ("Load cargo onto another structure.", struct_handler.handle_load),
	"locl": ("Broadcast a message to the local system.", social_handler.handle_locl),
	"nav": ("Get navigation information.", info_handler.handle_nav),
	"passwd": ("Change your password.", handle_passwd),
	"queue": ("List the assembly queue.", craft_handler.handle_queue),
	"rename": ("Rename your structure.", info_handler.handle_rename),
	"rep": ("View or set personal operator reputations.", faction_handler.handle_rep),
	"repf": ("View or set personal faction reputations.", faction_handler.handle_repf),
	"scan": ("Scan nearby structures.", info_handler.handle_scan),
	"set": ("Change the power setting of installed outfits.", struct_handler.handle_set),
	"status": ("Show status of your structure.", info_handler.handle_status),
	"subs": ("Send subspace message to another user.", social_handler.handle_subs),
	"supply": ("Supply energy to a docked structure.", struct_handler.handle_supply),
	"target": ("View or add combat targets.", combat_handler.handle_target),
	"uninstall": ("Uninstall an outfit into cargo.", struct_handler.handle_uninstall),
	"username": ("Change your username.", handle_username),
}

def handle_command(c: Client, cmd: str, args: List[str]) -> None:
	if cmd in COMMANDS:
		COMMANDS[cmd][1](c, args)
	else:
		c.send(HELP_MESSAGE, (cmd,))
	if cmd != "exit":
		c.prompt()

def handle_login(c: Client, cmd: str, args: List[str]) -> None:
	if cmd == "login":
		if len(args) < 2:
			c.send("Usage: login <username> <password>.")
			c.prompt()
			return
		username = args.pop(0)
		if c.login(username, " ".join(args)):
			for c2 in network.clients:
				if c2 != c and c2.username == username:
					c2.send("You have been disconnected by another session.")
					c2.quitting = True
					c.send("Disconnected an existing session from %s.", (c2.get_ip(),))
			c.send("\033[2J\033[H" + client.WELCOME_MESSAGE)
			c.send("Logged in as %s.", (username,))
			if c.email == None:
				c.send("WARNING: Please set an email address with the `email` command. This is used only for resetting your password.")
		elif c.quitting:
			return
		else:
			c.send("Incorrect username or password.")
	elif cmd == "register":
		if len(args) < 2:
			c.send("Usage: register <username> <password>. Username and password cannot contain spaces.")
			c.prompt()
			return
		if not c.checkvalid(args[0]):
			c.send("Username can only contain letters and numbers.")
		elif database.get_user_by_username(args[0]) != None:
			c.send("Username '%s' is already taken.", (args[0],))
		else:
			client.register_user(args.pop(0), " ".join(args))
			c.send("Registration successful! Try logging in with 'login [username] [password]'.")
	elif cmd == "exit":
		c.quit()
		return
	else:
		c.send("You are not logged in; use 'login [username] [password]' to log in, or 'register [username] [password]' to create a new account.")
	c.prompt()

def handle_death(c: Client) -> None:
	c.send("Your structure was destroyed.")
	c.send("Log in again to respawn.")
	c.quitting = True


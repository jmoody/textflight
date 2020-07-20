import logging
from typing import List

import database
import client
import system
import network
import strings
import handlers.combat_handler as combat_handler
import handlers.craft_handler as craft_handler
import handlers.faction_handler as faction_handler
import handlers.info_handler as info_handler
import handlers.ship_handler as ship_handler
import handlers.social_handler as social_handler
import handlers.struct_handler as struct_handler
import handlers.user_handler as user_handler
from client import Client, ChatMode, MessageType

def handle_help(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		for k, v in COMMANDS.items():
			c.send("{command}: {description}", command=k, description=c.translate(v[0]))
	else:
		cmd = args[0]
		if not cmd in COMMANDS:
			c.send(strings.MISC.NO_COMMAND, command=cmd)
		else:
			c.send("{command}: {description}", command=cmd, description=c.translate(COMMANDS[cmd][0]))

COMMANDS = {
	"airlock": ("Remove someone from your structure.", struct_handler.handle_airlock),
	"base": ("Construct a planetary base.", craft_handler.handle_base),
	"beam": ("Beam onto another structure.", struct_handler.handle_beam),
	"cancel": ("Cancel a queued assembly. Yields no resources.", craft_handler.handle_cancel),
	"capture": ("Attempt to capture a nearby structure.", combat_handler.handle_capture),
	"chat": ("Toggles chat on or off.", user_handler.handle_chat),
	"construct": ("Construct a new structure.", craft_handler.handle_construct),
	"craft": ("Queue an item for assembly.", craft_handler.handle_craft),
	"crate": ("Unpack a crate.", user_handler.handle_crate),
	"destroy": ("Destroy a nearby structure.", combat_handler.handle_destroy),
	"dock": ("Dock to a nearby structure.", ship_handler.handle_dock),
	"eject": ("Disconnect docked structures.", struct_handler.handle_eject),
	"email": ("Set your email address.", user_handler.handle_email),
	"exit": ("Disconnect from server.", user_handler.handle_exit),
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
	"faction_release": ("Release your faction's claim on a system or planet.", faction_handler.handle_release),
	"faction_rename": ("Rename your faction.", faction_handler.handle_rename),
	"faction_rep": ("View or set operator reputations.", faction_handler.handle_frep),
	"faction_repf": ("View or set faction reputations.", faction_handler.handle_frepf),
	"glob": ("Broadcast a message to the entire universe.", social_handler.handle_glob),
	"hail": ("Hail a structure.", social_handler.handle_hail),
	"help": ("Show list of commands, or usage of a given command.", handle_help),
	"install": ("Install an outfit from cargo.", struct_handler.handle_install),
	"jettison": ("Discard cargo into space.", craft_handler.handle_jettison),
	"jump": ("Jump to another system.", ship_handler.handle_jump),
	"land": ("Land on a planet.", ship_handler.handle_land),
	"language": ("Set your language.", user_handler.handle_language),
	"launch": ("Launch off a planet.", ship_handler.handle_launch),
	"load": ("Load cargo onto another structure.", struct_handler.handle_load),
	"locl": ("Broadcast a message to the local system.", social_handler.handle_locl),
	"nav": ("Get navigation information.", info_handler.handle_nav),
	"passwd": ("Change your password.", user_handler.handle_passwd),
	"queue": ("List the assembly queue.", craft_handler.handle_queue),
	"rdock": ("Remotely dock a structure.", ship_handler.handle_rdock),
	"redeem": ("Redeems a code to unlock premium status.", user_handler.handle_redeem),
	"rep": ("View or set personal operator reputations.", faction_handler.handle_rep),
	"repf": ("View or set personal faction reputations.", faction_handler.handle_repf),
	"scan": ("Scan nearby structures.", info_handler.handle_scan),
	"set": ("Change the power setting of installed outfits.", struct_handler.handle_set),
	"status": ("Show status of your structure.", info_handler.handle_status),
	"subs": ("Send subspace message to another user.", social_handler.handle_subs),
	"supply": ("Supply energy to a docked structure.", struct_handler.handle_supply),
	"swap": ("Swaps the order of two outfits.", struct_handler.handle_swap),
	"target": ("View or add combat targets.", combat_handler.handle_target),
	"trans": ("Transfer control core to another structure.", struct_handler.handle_trans),
	"uninstall": ("Uninstall an outfit into cargo.", struct_handler.handle_uninstall),
	"username": ("Change your username.", user_handler.handle_username),
}

def handle_command(c: Client, cmd: str, args: List[str]) -> None:
	if cmd in COMMANDS:
		COMMANDS[cmd][1](c, args)
	else:
		c.send(strings.MISC.HELP_MESSAGE, command=cmd)
	if cmd != "exit":
		c.prompt()

def handle_login(c: Client, cmd: str, args: List[str]) -> None:
	if cmd == "login":
		if len(args) < 2:
			c.send(strings.USAGE.LOGIN)
			c.prompt()
			return
		username = args.pop(0)
		if c.login(username, " ".join(args)):
			for c2 in network.clients:
				if c2 != c and c2.username == username:
					c2.send(strings.MISC.DISCONNECTED_BY)
					c2.quitting = True
					c.send(strings.MISC.DISCONNECTED_EXISTING, ip=c2.get_ip())
			c.send("\033[2J\033[H" + strings.MISC.WELCOME_MESSAGE)
			c.send(strings.MISC.LOGGED_IN, username=username)
			c.send(strings.MISC.CLIENTS_CONNECTED, num=len(network.clients))
			logging.info("Client '%s' logged in as %d ('%s').", c.get_ip(), c.id, username)
			for cl in network.clients:
				if cl.id != None and cl.chat_mode.value >= ChatMode.GLOBAL.value:
					message = cl.translate(strings.MISC.JOINED).format(username=c.username)
					cl.chat(MessageType.GLOBAL, "", message)
			if c.email == None:
				c.send(strings.MISC.EMAIL_WARNING)
		elif c.quitting:
			return
		else:
			logging.info("Failed login attempt from '%s', username '%s'.", c.get_ip(), username)
			c.send(strings.MISC.INCORRECT_LOGIN)
	elif cmd == "register":
		if len(args) < 2:
			c.send(strings.USAGE.REGISTER)
			c.prompt()
			return
		if not c.checkvalid(args[0]):
			c.send(strings.MISC.ALPHANUM_USERNAME)
		elif database.get_user_by_username(args[0]) != None:
			c.send(strings.MISC.USERNAME_TAKEN, username=args[0])
		else:
			username = args.pop(0)
			client.register_user(username, " ".join(args))
			logging.info("Client '%s' registered account '%s'.", c.get_ip(), username)
			c.send(strings.MISC.REGISTERED)
	elif cmd == "language":
		handle_language(c, args)
	elif cmd == "exit":
		c.quit()
		return
	else:
		c.send(strings.MISC.NOT_LOGGED_IN)
	c.prompt()

def handle_death(c: Client) -> None:
	c.send(strings.MISC.STRUCT_DESTROYED)
	c.quitting = True


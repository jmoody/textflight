import gettext
import bcrypt
import time
import re
import combat
from enum import Enum
from threading import Lock
from typing import Tuple

import database
import structure
import config
from outfit import Outfit
from cargo import Cargo

WELCOME_MESSAGE = """ _              _     __  _  _  __ _  _     _
| |_  ___ __ __| |_  / _|| |(_)/ _` || |_  | |_
|  _|/ -_)\ \ /|  _||  _|| || |\__. ||   \ |  _|
 \__|\___|/_\_\ \__||_|  |_||_||___/ |_||_| \__|

TEXTFLIGHT remote access protocol v0.1a.
Protocol manual available for transfer: https://leagueh.xyz/tf/"""
ccf = config.get_section("client")
SPAWN_TIME = ccf.getint("SpawnTime")

conn = database.conn
VALIDREGEX = re.compile(ccf.get("ValidateRegex"))

class MessageType(Enum):
	SUBSPACE = "SUBS"
	LOCAL = "LOCL"
	HAIL = "HAIL"
	FACTION = "FACT"

class Client:
	read_buffer = ""
	write_buffer = bytes()
	write_lock = Lock()
	msg_buffer = []
	quitting = False
	
	id = None
	
	def __init__(self, sock) -> None:
		self.sock = sock
		self.tree = set()
		self.send(WELCOME_MESSAGE)
		self.prompt()
	
	def fileno(self) -> int:
		return self.sock.fileno()
	
	def checkvalid(self, text: str) -> str:
		return len(text) == len(VALIDREGEX.sub("", text))
	
	def get_ip(self) -> int:
		return self.sock.getpeername()[0]
	
	def translate(self, message: str) -> str:
		return gettext.gettext(message)
	
	def chat(self, mtype: MessageType, author: str, message: str) -> None:
		msg = "[%s][%s] %s" % (mtype.value, author, message)
		self.msg_buffer.append(msg)
	
	def send(self, message: str, args = None) -> None:
		msg = ""
		for m in self.msg_buffer:
			msg+= m + "\n"
		self.msg_buffer = []
		msg+= self.translate(message) + "\n"
		if args != None:
			msg = msg % args
		self.send_bytes(msg.encode("utf-8"))
	
	def prompt(self) -> None:
		self.send_bytes("> ".encode("utf-8"))
	
	def send_bytes(self, message) -> None:
		self.write_lock.acquire()
		self.write_buffer+= message
		self.write_lock.release()
	
	def quit(self) -> None:
		self.send("Goodbye.")
		self.quitting = True
	
	def set_email(self, email: str) -> None:
		conn.execute("UPDATE users SET email = ? WHERE id = ?;", (email, self.id))
		conn.commit()
		self.email = email
	
	def set_password(self, password: str) -> None:
		passwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
		conn.execute("UPDATE users SET passwd = ? WHERE id = ?;", (passwd, self.id))
		conn.commit()
	
	def set_username(self, username: str) -> bool:
		c = conn.cursor()
		if c.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone() != None:
			return False
		c.execute("UPDATE users SET username = ? WHERE id = ?;", (username, self.id))
		conn.commit()
		self.username = username
		return True
	
	def set_chat(self, chat: bool) -> None:
		self.chat_on = chat
		conn.execute("UPDATE users SET chat_on = ? WHERE id = ?;", (int(chat), self.id))
		conn.commit()
	
	def login(self, username: str, password: str) -> bool:
		c = conn.cursor()
		c.execute("SELECT * FROM users WHERE username = ?;", (username,))
		ctup = c.fetchone()
		if ctup == None or not bcrypt.checkpw(password.encode("utf-8"), ctup["passwd"]):
			return False
		self.id = ctup["id"]
		self.username = ctup["username"]
		self.email = ctup["email"]
		self.faction_id = ctup["faction_id"]
		self.chat_on = bool(ctup["chat_on"])
		self.premium = bool(ctup["premium"])
		c.execute("SELECT * FROM structures WHERE id = ?;", (ctup["structure_id"],))	
		self.structure = structure.load_structure(ctup["structure_id"])
		if self.structure == None:
			respawn = ctup["last_spawn"] + SPAWN_TIME - time.time()
			if respawn > 0:
				self.send("Please wait %d seconds before respawning.", (respawn,))
				self.quitting = True
				return False
			self.structure = create_starter_ship(self.id, ctup["username"])
			conn.execute("UPDATE users SET structure_id = ?, last_spawn = strftime('%s', 'now') WHERE id = ?;",
				(self.structure.id, self.id))
		conn.execute("UPDATE users SET last_login = strftime('%s', 'now') WHERE id = ?", (self.id,))
		conn.commit()
		combat.update_targets(self.structure.system.id)
		return True

def create_starter_ship(uid, username) -> structure.Structure:
	ship = structure.create_structure(username + "'s Ship", uid, "ship", 8, 0)
	Outfit("Fusion Reactor", 1).install(ship)
	Outfit("Solar Array", 1).install(ship)
	Outfit("Coolant Pump", 1).install(ship)
	Outfit("Shield Matrix", 1).install(ship)
	Outfit("Warp Engine", 1).install(ship)
	Outfit("Antigravity Engine", 1).install(ship)
	Outfit("Mining Beam", 1).install(ship)
	Outfit("Assembler", 1).install(ship)
	Cargo("Hydrogen Fuel Cell", 8).add(ship)
	return ship

def register_user(username, password) -> None:
	passwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
	user_id = conn.execute("INSERT INTO users (username, passwd) VALUES (?, ?);", (username, passwd)).lastrowid
	conn.commit()


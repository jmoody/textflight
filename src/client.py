import bcrypt
import time
import re
import logging
import math
from enum import Enum
from threading import Lock
from datetime import datetime

import combat
import database
import structure
import config
import system
import strings
import translations
import quest
from outfit import Outfit
from cargo import Cargo

class ChatMode(Enum):
	OFF = 0
	DIRECT = 1
	LOCAL = 2
	GLOBAL = 3

ccf = config.get_section("client")
SPAWN_TIME = ccf.getint("SpawnTime")

conn = database.conn
DAY = 60 * 60 * 24
VALIDREGEX = re.compile(ccf.get("ValidateRegex"))

ERROR_COLOUR = "\033[31m"
RESET_COLOUR = "\033[0m"

class MessageType(Enum):
	SUBSPACE = "SUBS"
	LOCAL = "LOCL"
	HAIL = "HAIL"
	FACTION = "FACT"
	GLOBAL = "GLOB"

class Client:
	read_buffer = ""
	write_buffer = bytes()
	msg_buffer = []
	quitting = False
	translator = translations.get_default()
	client_mode = False
	display_streak_message = False
	
	id = None
	username = None
	
	def __init__(self, sock) -> None:
		self.sock = sock
		self.tree = set()
		self.session_start = time.time()
		self.last_command = time.time()
		self.send(strings.MISC.WELCOME_MESSAGE, version=config.VERSION)
		self.prompt()
	
	def fileno(self) -> int:
		return self.sock.fileno()
	
	def checkvalid(self, text: str) -> str:
		return len(text) == len(VALIDREGEX.sub("", text))
	
	def get_ip(self) -> int:
		try:
			return self.sock.getpeername()[0]
		except:
			return "[socket closed]"
	
	def translate(self, message: str) -> str:
		return self.translator.gettext(message)
	
	def chat(self, mtype: MessageType, author: str, message: str) -> None:
		msg = message
		if author != "":
			msg = "[%s][%s] %s" % (mtype.value, author, message)
		self.msg_buffer.append(msg)
	
	def send(self, message: str, error = False, args = None, **kwargs) -> None:
		msg = ""
		if self.client_mode:
			msg+= message + "|" + self.translate(message)
			for k, v in kwargs.items():
				msg+= "|%s=%s" % (k, v)
			msg+= "\n"
		else:
			msg+= self.translate(message) + "\n"
			msg = msg.format(**kwargs)
		if error:
			msg = ERROR_COLOUR + msg + RESET_COLOUR
		self.send_bytes(msg.encode("utf-8"))
	
	def prompt(self) -> None:
		msg = ""
		for m in self.msg_buffer:
			msg+= m + "\n"
		self.msg_buffer = []
		msg+= "> "
		self.send_bytes(msg.encode("utf-8"))
	
	def send_bytes(self, message) -> None:
		self.write_buffer+= message
	
	def quit(self) -> None:
		self.send(strings.MISC.GOODBYE)
		self.quitting = True
	
	def set_email(self, email: str) -> None:
		conn.execute("UPDATE users SET email = ? WHERE id = ?;", (email, self.id))
		conn.commit()
		self.email = email
	
	def set_language(self, lang: str) -> None:
		if lang == "client":
			self.client_mode = True
			self.language = translations.languages["en"]
			return
		conn.execute("UPDATE users SET language = ? WHERE id = ?;", (lang, self.id))
		conn.commit()
		self.language = translations.languages[lang]
	
	def set_password(self, password: str) -> None:
		passwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
		conn.execute("UPDATE users SET passwd = ? WHERE id = ?;", (passwd, self.id))
		conn.commit()
	
	def redeem_code(self, code: str) -> bool:
		if conn.execute("DELETE FROM keys WHERE id = ?;", (code,)).rowcount > 0:
			conn.execute("UPDATE users SET premium = 1 WHERE id = ?;", (self.id,))
			self.premium = True
			conn.commit()
			return True
		return False
	
	def set_username(self, username: str) -> bool:
		c = conn.cursor()
		if c.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchone() != None:
			return False
		c.execute("UPDATE users SET username = ? WHERE id = ?;", (username, self.id))
		conn.commit()
		self.username = username
		logging.info("User %d changed their username to '%s'.", self.id, username)
		return True
	
	def set_chat(self, chat_mode: ChatMode) -> None:
		self.chat_mode = chat_mode
		conn.execute("UPDATE users SET chat_mode = ? WHERE id = ?;", (chat_mode.value, self.id))
		conn.commit()
	
	def login(self, username: str, password: str) -> bool:
		c = conn.cursor()
		c.execute("SELECT * FROM users WHERE username = ?;", (username,))
		ctup = c.fetchone()
		if ctup == None or not bcrypt.checkpw(password.encode("utf-8"), ctup["passwd"]):
			return False
		self.id = ctup["id"]
		self.created_at = ctup["created_at"]
		self.username = ctup["username"]
		self.email = ctup["email"]
		self.faction_id = ctup["faction_id"]
		chat_mode = ctup["chat_mode"]
		if chat_mode == 0:
			self.chat_mode = ChatMode.OFF
		elif chat_mode == 1:
			self.chat_mode = ChatMode.DIRECT
		elif chat_mode == 2:
			self.chat_mode = ChatMode.LOCAL
		elif chat_mode == 3:
			self.chat_mode = ChatMode.GLOBAL
		else:
			self.chat_mode = ChatMode.GLOBAL
			logging.warning("User %d has been set to invalid chat mode '%d'.", chat_mode)
		self.language = translations.languages[ctup["language"]]
		self.premium = bool(ctup["premium"])
		
		# Check that user is in a structure
		c.execute("SELECT * FROM structures WHERE id = ?;", (ctup["structure_id"],))	
		self.structure = structure.load_structure(ctup["structure_id"])
		if self.structure == None:
			respawn = ctup["last_spawn"] + SPAWN_TIME - time.time()
			if respawn > 0:
				logging.info("User %d attempted to respawn with %d seconds remaining.", self.id, respawn)
				self.send(strings.MISC.RESPAWN, remaining=respawn)
				self.quitting = True
				return False
			self.structure = create_starter_ship(self.id, ctup["username"])
			conn.execute("UPDATE users SET structure_id = ?, last_spawn = strftime('%s', 'now') WHERE id = ?;",
				(self.structure.id, self.id))
			logging.info("User %d spawned.", self.id)
		
		# Daily rewards
		self.streak = ctup["streak"]
		last_login_day = int(ctup["last_login"] / DAY)
		today = int(time.time() / DAY)
		if last_login_day < today - 1:
			self.streak = 0
			self.display_streak_message = True
		elif last_login_day < today:
			self.streak+= 1
			quality = int(pow(2, int(math.log2(self.streak))))
			quality = max(quality, 2)
			today = datetime.today()
			if today.month == 10 and today.day >= 24:
				theme = "halloween"
			else:
				theme = None
			Cargo("Crate", 1, quality, theme).add(self.structure)
			self.display_streak_message = True
		
		# Update database
		conn.execute("UPDATE users SET last_login = strftime('%s', 'now'), streak = ? WHERE id = ?", (self.streak, self.id))
		conn.execute("INSERT OR IGNORE INTO map (user_id, sys_id) VALUES (?, ?);", (self.id, self.structure.system.id_db))
		conn.commit()
		combat.update_targets(self.structure.system.id)
		return True

def create_starter_ship(uid, username) -> structure.Structure:
	ship = structure.create_structure(username + "'s Ship", uid, "ship", 8, system.System(0))
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
	quest.quests["Powering Up"].add(user_id)
	conn.commit()


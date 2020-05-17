import gettext
import bcrypt
from threading import Lock
from typing import Tuple

import database
import structure
from outfit import Outfit

WELCOME_MESSAGE = "Welcome to textflight!"
MOTD = "We're full of bugs!"

conn = database.conn

class Client:
	read_buffer = ""
	write_buffer = bytes()
	write_lock = Lock()
	quitting = False
	
	id = None
	
	def __init__(self, sock) -> None:
		self.sock = sock
		self.send(WELCOME_MESSAGE)
		self.send(MOTD)
		self.prompt()
	
	def fileno(self) -> int:
		return self.sock.fileno()
	
	def translate(self, message: str) -> str:
		return gettext.gettext(message)
	
	def send(self, message: str, args = None) -> None:
		msg = self.translate(message) + "\n"	# TODO: Allow setting the language
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
	
	def login(self, username: str, password: str) -> bool:
		c = conn.cursor()
		c.execute("SELECT * FROM users WHERE username = ?;", (username,))
		ctup = c.fetchone()
		if ctup == None or not bcrypt.checkpw(password.encode("utf-8"), ctup["passwd"]):
			return False
		self.id = ctup["id"]
		self.username = ctup["username"]
		self.email = ctup["email"]
		c.execute("SELECT * FROM structures WHERE id = ?;", (ctup["structure_id"],))	
		self.structure = structure.load_structure(ctup["structure_id"])
		if self.structure == None:
			self.structure = create_starter_ship(self.id, ctup["username"])
			conn.execute("UPDATE users SET structure_id = ? WHERE id = ?", (self.structure.id, self.id))
			conn.commit()
		return True

def create_starter_ship(uid, username) -> structure.Structure:
	ship = structure.create_structure(username + "'s Ship", uid, "ship", 8, 0)
	Outfit("Reactor", 1).install(ship)
	Outfit("Coolant Pump", 1).install(ship)
	Outfit("Shield Matrix", 1).install(ship)
	Outfit("Warp Engine", 1).install(ship)
	Outfit("Antigravity Engine", 1).install(ship)
	Outfit("Mining Beam", 1).install(ship)
	Outfit("Assembler", 1).install(ship)
	Outfit("Capacitor", 1).install(ship)
	return ship

def register_user(username, password) -> None:
	passwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
	user_id = conn.execute("INSERT INTO users (username, passwd) VALUES (?, ?);", (username, passwd)).lastrowid
	conn.commit()


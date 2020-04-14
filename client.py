import gettext
from threading import Lock
from typing import Tuple

import database
import structure

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
	
	def login(self, username, passwd) -> True:
		c = conn.cursor()
		c.execute("SELECT * FROM users WHERE username = ? AND passwd = ?;", (username, passwd))
		ctup = c.fetchone()
		if ctup == None:
			return False
		self.id = ctup["id"]
		self.username = ctup["username"]
		c.execute("SELECT * FROM structures WHERE id = ?;", (ctup["structure_id"],))	
		self.structure = structure.load_structure(ctup["structure_id"])		# TODO: Handle client structure being destroyed
		return True

def register_user(username, passwd) -> None:
	ship = structure.create_structure(username + "'s Ship", None, "ship", 16, 0)
	conn.cursor().execute("INSERT INTO users (username, passwd, structure_id) VALUES (?, ?, ?);", (username, passwd, ship.id))
	conn.commit()


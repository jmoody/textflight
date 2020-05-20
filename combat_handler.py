from typing import List

import faction
import production
import structure
import database
from client import Client

conn = database.conn

def handle_capture(c: Client, args: List[str]) -> None:
	pass

def handle_ceasefire(c: Client, args: List[str]) -> None:
	pass

def handle_destroy(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: destroy <structure ID>")
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	s = structure.load_structure(sid)
	if s == None or s.system.id != c.structure.system.id:
		c.send("Unable to locate structure.")
		return
	report = production.update(c.structure)
	if s.shield > 0:
		c.send("Cannot destroy structure while its shields are up.")
	elif report.electron_damage < s.outfit_space:
		c.send("Electron beams not powerful enough to destroy target.")
	else:
		s._destroyed = True
		conn.execute("UPDATE users SET structure_id = NULL WHERE structure_id = ?;", (s.id,))
		conn.execute("DELETE FROM structures WHERE id = ?;", (s.id,))
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.DESTROY_PENALTY)
		c.send("Destroyed structure '%d %s'.", (s.id, s.name))

def handle_target(c: Client, args: List[str]) -> None:
	pass


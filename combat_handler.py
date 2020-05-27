from typing import List

import faction
import production
import structure
import database
import combat
from client import Client

conn = database.conn

def handle_capture(c: Client, args: List[str]) -> None:
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
	elif report.hull_damage < s.outfit_space:
		c.send("Weapons not powerful enough to destroy target.")
	else:
		s._destroyed = True
		conn.execute("UPDATE users SET structure_id = NULL WHERE structure_id = ?;", (s.id,))
		conn.execute("DELETE FROM structures WHERE id = ?;", (s.id,))
		conn.commit()
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.DESTROY_PENALTY)
		combat.clear_targets(s)
		c.send("Destroyed structure '%d %s'.", (s.id, s.name))
		del s
		combat.update_targets(c.structure.system.id)

def handle_target(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		production.update(c.structure)
		if len(c.structure.targets) < 1:
			c.send("Weapons not targeting any structures.")
			return
		for target in c.structure.targets:
			c.send("%d %s", (target.id, target.name))
	elif len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send("Not a number.")
		if sid == c.structure.id:
			c.send("You cannot target yourself.")
			return
		for struct in c.structure.targets:
			if struct.id == sid:
				c.send("Already targeting '%d %s'.", (struct.id, struct.name))
				return
		s = structure.load_structure(sid)
		if s == None or s.system.id != c.structure.system.id:
			c.send("Unable to locate structure.")
			return
		report = production.update(c.structure)
		production.update(s, report.now)
		if report.electron_damage == 0 and report.plasma_damage == 0 and report.emp_damage == 0:
			c.send("Weapons are not online.")
			return
		combat.add_target(c.structure, s)
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.ATTACK_PENALTY)
		combat.update_targets(s.system.id)
		c.send("Targeting structure '%d %s'.", (s.id, s.name))
	else:
		c.send("Usage: target <structure ID>")


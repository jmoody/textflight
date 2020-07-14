import logging
import time
from typing import List

import faction
import production
import structure
import database
import combat
import strings
from client import Client

conn = database.conn

def handle_capture(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.CAPTURE)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	s = structure.load_structure(sid)
	now = time.time()
	if s == None or s.system.id != c.structure.system.id:
		c.send(strings.MISC.NO_STRUCT)
		return
	elif now - s.created_at < combat.SPAWN_SAFE:
		c.send(strings.COMBAT.SAFE, remaining=round(combat.SPAWN_SAFE - now + s.created_at))
		return
	report = production.update(c.structure)
	report2 = production.update(s)
	if s.shield > 0:
		c.send(strings.COMBAT.SHIELDS_UP)
		return
	elif report.crew < 1:
		c.send(strings.COMBAT.NO_H2H)
		return
	
	# Determine casualties
	ratio = (report2.defence * report2.crew) / (report.attack * report.crew)
	deaths2 = report2.crew
	deaths1 = report2.crew * ratio
	if deaths1 > report.crew:
		deaths1 = report.crew
		deaths2 = report.crew / ratio
	report.crew-= deaths1
	c.send(strings.COMBAT.CASUALTIES, enemy=int(deaths2), friendly=int(deaths1))
	
	# Apply casualties for our ship
	for outfit in report.living_spaces:
		if outfit.counter >= deaths1:
			outfit.set_counter(outfit.counter - deaths1)
			break
		deaths1-= outfit.counter
	
	# Apply casualties for enemy ship
	for outfit in report2.living_spaces:
		if outfit.counter >= deaths2:
			outfit.set_counter(outfit.counter - deaths2)
			break
		deaths2-= outfit.counter
		outfit.set_counter(0)
		outfit.set_counter(0)
	
	if report.crew < 1:
		c.send(strings.COMBAT.CAPTURE_FAILED)
	else:
		s.owner_id = c.id
		conn.execute("UPDATE structures SET owner_id = ? WHERE id = ?;", (c.id, s.id))
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.CAPTURE_PENALTY)
		c.send(strings.COMBAT.CAPTURE_SUCCEEDED)
		combat.update_targets(c.structure.system.id)

def handle_destroy(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.DESTROY)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	s = structure.load_structure(sid)
	now = time.time()
	if s == None or s.system.id != c.structure.system.id:
		c.send(strings.MISC.NO_STRUCT)
		return
	elif now - s.created_at < combat.SPAWN_SAFE:
		c.send(strings.COMBAT.SAFE, remaining=round(combat.SPAWN_SAFE - now + s.created_at))
		return
	report = production.update(c.structure)
	production.update(s)
	if s.shield > 0:
		c.send(strings.COMBAT.SHIELDS_UP)
	elif report.hull_damage < s.outfit_space:
		c.send(strings.COMBAT.NOT_POWERFUL)
	else:
		s._destroyed = True
		conn.execute("UPDATE users SET structure_id = NULL WHERE structure_id = ?;", (s.id,))
		conn.execute("UPDATE structures SET dock_id = NULL WHERE dock_id = ?;", (s.id,))
		if s.dock_parent != None:
			s.dock_parent.dock_children.remove(s)
		else:
			for struct in s.dock_children:
				struct.dock_parent = None
		conn.execute("DELETE FROM structures WHERE id = ?;", (s.id,))
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.DESTROY_PENALTY)
		combat.clear_targets(s)
		logging.info("Structure '%d %s' destroyed by %d.", s.id, s.name, c.id)
		c.send(strings.COMBAT.DESTROYED, id=s.id, name=s.name)
		del s
		combat.update_targets(c.structure.system.id)

def handle_target(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		production.update(c.structure)
		if len(c.structure.targets) < 1:
			c.send(strings.COMBAT.NO_TARGETS)
			return
		for target in c.structure.targets:
			c.send(strings.COMBAT.TARGET, id=target.id, name=target.name)
	elif len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send(strings.MISC.NAN)
		now = time.time()
		if sid == c.structure.id:
			c.send(strings.COMBAT.TARGET_SELF)
			return
		elif now - c.structure.created_at < combat.SPAWN_SAFE:
			c.send(strings.COMBAT.SAFE_NOTARGET, remaining=round(combat.SPAWN_SAFE - now + c.structure.created_at))
			return
		for struct in c.structure.targets:
			if struct.id == sid:
				c.send(strings.COMBAT.ALREADY_TARGETING, id=struct.id, name=struct.name)
				return
		s = structure.load_structure(sid)
		if s == None or s.system.id != c.structure.system.id:
			c.send(strings.MISC.NO_STRUCT)
			return
		elif now - s.created_at < combat.SPAWN_SAFE:
			c.send(strings.COMBAT.SAFE, remaining=round(combat.SPAWN_SAFE - now + s.created_at))
			return
		report = production.update(c.structure)
		production.update(s, report.now)
		if not report.has_weapons:
			c.send(strings.COMBAT.NO_WEAPONS)
			return
		combat.add_target(c.structure, s)
		faction.apply_penalty(c.id, c.faction_id, s.owner_id, faction.ATTACK_PENALTY)
		combat.update_targets(s.system.id)
		logging.info("User %d targeting structures '%d %s'.", (c.id, s.id, s.name))
		c.send(strings.COMBAT.TARGETING, id=s.id, name=s.name)
	else:
		c.send(strings.USAGE.TARGET)


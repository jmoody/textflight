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
	if s.shield > 0:
		c.send(strings.COMBAT.SHIELDS_UP)
	elif report.hull_damage < s.outfit_space:
		c.send(strings.COMBAT.NOT_POWERFUL)
	else:
		s._destroyed = True
		conn.execute("UPDATE users SET structure_id = NULL WHERE structure_id = ?;", (s.id,))
		conn.execute("DELETE FROM structures WHERE id = ?;", (s.id,))
		conn.commit()
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


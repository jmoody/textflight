from typing import List

import production
import system
import database
import structure
import faction
import combat
import strings
from client import Client

conn = database.conn

def handle_dock(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send(strings.USAGE.DOCK, error=True)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	if sid == s.id:
		c.send(strings.SHIP.SELF_DOCK, error=True)
		return
	elif s.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS, error=True)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.ALREADY_DOCKED, error=True)
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id or target.planet_id != s.planet_id:
		c.send(strings.MISC.NO_STRUCT, error=True)
	elif target.dock_parent != None:
		c.send(strings.SHIP.TARGET_ALREADY_DOCKED, error=True)
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send(strings.MISC.PERMISSION_DENIED, error=True)
	else:
		target.dock_children.append(s)
		s.dock_parent = target
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (sid, s.id))
		production.update(s, send_updates=True)
		c.send(strings.SHIP.DOCKED_TO, id=sid, name=target.name)

def handle_rdock(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send(strings.USAGE.RDOCK, error=True)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	if sid == s.id:
		c.send(strings.SHIP.SELF_DOCK, error=True)
		return
	elif s.dock_parent != None:
		c.send(strings.SHIP.ALREADY_DOCKED, error=True)
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id:
		c.send(strings.MISC.NO_STRUCT, error=True)
	elif target.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS, error=True)
	elif target.dock_parent != None or len(target.dock_children) > 0:
		c.send(strings.SHIP.TARGET_ALREADY_DOCKED, error=True)
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send(strings.MISC.PERMISSION_DENIED, error=True)
	else:
		s.dock_children.append(target)
		target.dock_parent = s
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (s.id, sid))
		production.update(s, send_updates=True)
		c.send(strings.SHIP.DOCKED, id=sid, name=target.name)

def handle_land(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.LAND, error=True)
		return
	try:
		pid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	if pid > len(c.structure.system.planets) - 1:
		c.send(strings.SHIP.NO_PLANET, error=True)
		return
	elif c.structure.planet_id != None:
		c.send(strings.SHIP.ALREADY_LANDED, error=True)
		return
	elif c.structure.dock_parent != None or len(c.structure.dock_children) > 0:
		c.send(strings.SHIP.LAND_WHILE_DOCKED, error=True)
		return
	report = production.update(c.structure)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send(strings.SHIP.NO_ANTIGRAVITY, error=True)
		else:
			c.send(strings.SHIP.LESS_ANTIGRAVITY, error=True)
		return
	c.structure.planet_id = pid
	c.structure.mining_progress = 0
	conn.execute("UPDATE structures SET planet_id = ?, mining_progress = 0 WHERE id = ?;", (pid, c.structure.id))
	c.send(strings.SHIP.LANDED, planet=pid)
	production.update(c.structure, send_updates=True)

def handle_launch(c: Client, args: List[str]) -> None:
	s = c.structure
	if s.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS_LAUNCH, error=True)
		return
	elif s.planet_id == None:
		c.send(strings.SHIP.NOT_LANDED, error=True)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.LAUNCH_WHILE_DOCKED, error=True)
		return
	report = production.update(s)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send(strings.SHIP.NO_ANTIGRAVITY, error=True)
		else:
			c.send(strings.SHIP.LESS_ANTIGRAVITY, error=True)
		return
	s.planet_id = None
	s.mining_progress = 0
	conn.execute("UPDATE structures SET planet_id = NULL, mining_progress = 0 WHERE id = ?;", (s.id,))
	c.send(strings.SHIP.LAUNCHED)
	production.update(c.structure, send_updates=True)

def handle_jump(c: Client, args: List[str]) -> None:
	
	# Validate input
	s = c.structure
	if len(args) < 1:
		c.send(strings.USAGE.JUMP, error=True)
		return
	elif s.planet_id != None:
		c.send(strings.SHIP.WARP_ON_PLANET, error=True)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.WARP_WHILE_DOCKED, error=True)
		return
	sids = []
	try:
		lindex = int(args.pop(0))
		for arg in args:
			sids.append(int(arg))
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	links = s.system.get_links()
	if lindex >= len(links) or links[lindex] == None:
		c.send(strings.SHIP.NO_SYSTEM, error=True)
		return
	report = production.update(s)
	if s.warp_charge < report.mass:
		c.send(strings.SHIP.NO_CHARGE, error=True)
		return
	
	# Make sure all ships are ready to jump
	ships = {s: report.mass}
	for sid in sids:
		fship = structure.load_structure(sid)
		if fship == None or fship.system.id != s.system.id:
			c.send(strings.SHIP.NO_STRUCTURE_X, id=sid, error=True)
			return
		elif conn.execute("SELECT id FROM users WHERE structure_id = ?;", (sid,)).fetchone() != None:
			c.send(strings.SHIP.PERMISSION_DENIED_X, id=sid, name=fship.name, error=True)
			return
		elif not faction.has_permission(c, fship, faction.JUMP_MIN):
			c.send(strings.SHIP.PERMISSION_DENIED_X, id=sid, name=fship.name, error=True)
			return
		freport = production.update(fship)
		if fship.warp_charge < freport.mass:
			c.send(strings.SHIP.NO_CHARGE_X, id=sid, name=fship.name, error=True)
			return
		ships[fship] = report.mass
	
	# Perform jump
	lid, drag, xo, yo = links[lindex]
	sys = system.System(lid)
	for ship, mass in ships.items():
		cost = report.mass / pow(2, system.DRAG_BITS) * drag
		ship.system = sys
		ship.warp_charge-= cost
		ship.mining_progress = 0
		conn.execute("UPDATE structures SET sys_id = ?, warp_charge = ?, mining_progress = 0 WHERE id = ?",
			(sys.id_db, ship.warp_charge, ship.id))
	c.send(strings.SHIP.ENGAGING)
	conn.execute("INSERT OR IGNORE INTO map (user_id, sys_id) VALUES (?, ?);", (c.id, sys.id_db))
	production.update(s, send_updates=True)
	combat.clear_targets(s)
	combat.update_targets(sys.id)
	c.send(strings.SHIP.JUMP_COMPLETE, charge=round(s.warp_charge / report.mass * 100))
	production.update(c.structure, send_updates=True)


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
		c.send(strings.USAGE.DOCK)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if sid == s.id:
		c.send(strings.SHIP.SELF_DOCK)
		return
	elif s.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.ALREADY_DOCKED)
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id:
		c.send(strings.MISC.NO_STRUCT)
	elif target.dock_parent != None:
		c.send(strings.SHIP.TARGET_ALREADY_DOCKED)
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send(strings.MISC.PERMISSION_DENIED)
	else:
		target.dock_children.append(s)
		s.dock_parent = target
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (sid, s.id))
		conn.commit()
		c.send(strings.SHIP.DOCKED_TO, id=sid, name=target.name)

def handle_rdock(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send(strings.USAGE.RDOCK)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if sid == s.id:
		c.send(strings.SHIP.SELF_DOCK)
		return
	elif s.dock_parent != None:
		c.send(strings.SHIP.ALREADY_DOCKED)
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id:
		c.send(strings.MISC.NO_STRUCT)
	elif target.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS)
	elif target.dock_parent != None or len(target.dock_children) > 0:
		c.send(strings.SHIP.TARGET_ALREADY_DOCKED)
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send(strings.MISC.PERMISSION_DENIED)
	else:
		s.dock_children.append(target)
		target.dock_parent = s
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (s.id, sid))
		conn.commit()
		c.send(strings.SHIP.DOCKED, id=sid, name=target.name)

def handle_land(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.LAND)
		return
	try:
		pid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if pid > len(c.structure.system.planets):
		c.send(strings.SHIP.NO_PLANET)
		return
	elif c.structure.planet_id != None:
		c.send(strings.SHIP.ALREADY_LANDED)
		return
	elif c.structure.dock_parent != None or len(c.structure.dock_children) > 0:
		c.send(strings.SHIP.LAND_WHILE_DOCKED)
		return
	report = production.update(c.structure)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send(strings.SHIP.NO_ANTIGRAVITY)
		else:
			c.send(strings.SHIP.LESS_ANTIGRAVITY)
		return
	c.structure.planet_id = pid
	c.structure.mining_progress = 0
	conn.execute("UPDATE structures SET planet_id = ?, mining_progress = 0 WHERE id = ?;", (pid, c.structure.id))
	conn.commit()
	c.send(strings.SHIP.LANDED, planet=pid)

def handle_launch(c: Client, args: List[str]) -> None:
	s = c.structure
	if s.type != "ship":
		c.send(strings.SHIP.ONLY_SHIPS_LAUNCH)
		return
	elif s.planet_id == None:
		c.send(strings.SHIP.NOT_LANDED)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.LAUNCH_WHILE_DOCKED)
		return
	report = production.update(s)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send(strings.SHIP.NO_ANTIGRAVITY)
		else:
			c.send(strings.SHIP.LESS_ANTIGRAVITY)
		return
	s.planet_id = None
	s.mining_progress = 0
	conn.execute("UPDATE structures SET planet_id = NULL, mining_progress = 0 WHERE id = ?;", (s.id,))
	conn.commit()
	c.send(strings.SHIP.LAUNCHED)

def handle_jump(c: Client, args: List[str]) -> None:
	
	# Validate input
	s = c.structure
	if len(args) < 1:
		c.send(strings.USAGE.JUMP)
		return
	elif s.planet_id != None:
		c.send(strings.SHIP.WARP_ON_PLANET)
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send(strings.SHIP.WARP_WHILE_DOCKED)
		return
	sids = []
	try:
		lindex = int(args.pop(0))
		for arg in args:
			sids.append(int(arg))
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	links = s.system.get_links()
	if lindex >= len(links):
		c.send(strings.SHIP.NO_SYSTEM)
		return
	report = production.update(s)
	if s.warp_charge < report.mass:
		c.send(strings.SHIP.NO_CHARGE)
		return
	
	# Make sure all ships are ready to jump
	ships = {s: report.mass}
	for sid in sids:
		fship = structure.load_structure(sid)
		if fship == None or fship.system.id != s.system.id:
			c.send(strings.SHIP.NO_STRUCTURE_X, id=sid)
			return
		elif conn.execute("SELECT id FROM users WHERE structure_id = ?;", (sid,)).fetchone() != None:
			c.send(strings.SHIP.PERMISSION_DENIED_X, id=sid, name=fship.name)
			return
		elif not faction.has_permission(c, fship, faction.JUMP_MIN):
			c.send(strings.SHIP.PERMISSION_DENIED_X, id=sid, name=fship.name)
			return
		freport = production.update(fship)
		if fship.warp_charge < freport.mass:
			c.send(strings.SHIP.NO_CHARGE_X, id=sid, name=fship.name)
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
	conn.commit()
	combat.clear_targets(s)
	combat.update_targets(sys.id)
	c.send(strings.SHIP.JUMP_COMPLETE, charge=round(s.warp_charge / report.mass * 100))


from typing import List

import production
import system
import database
import structure
import faction
import combat
from client import Client

conn = database.conn

def handle_dock(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send("Usage: dock <structure ID>")
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if sid == s.id:
		c.send("Cannot dock to yourself.")
		return
	elif s.type != "ship":
		c.send("Only ships can be docked to a structure.")
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send("Already docked to a structure.")
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id:
		c.send("Unable to locate structure.")
	elif target.dock_parent != None:
		c.send("Target is already docked to a structure.")
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send("Permission denied.")
	else:
		target.dock_children.append(s)
		s.dock_parent = target
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (sid, s.id))
		conn.commit()
		c.send("Docked to structure '%d %s'.", (sid, target.name))

def handle_rdock(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send("Usage: rdock <structure ID>")
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if sid == s.id:
		c.send("Cannot dock to yourself.")
		return
	elif s.dock_parent != None:
		c.send("Already docked to a structure.")
		return
	target = structure.load_structure(sid)
	if target == None or target.system.id != s.system.id:
		c.send("Unable to locate structure.")
	elif target.type != "ship":
		c.send("Only ships can be docked to a structure.")
	elif target.dock_parent != None or len(target.dock_children) > 0:
		c.send("Target is already docked to a structure.")
	elif not faction.has_permission(c, target, faction.DOCK_MIN):
		c.send("Permission denied.")
	else:
		s.dock_children.append(target)
		target.dock_parent = s
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (s.id, sid))
		conn.commit()
		c.send("Docked structure '%d %s'.", (sid, target.name))

def handle_land(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: land <planet ID>")
		return
	try:
		pid = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if pid > len(c.structure.system.planets):
		c.send("Planet does not exist.")
		return
	elif c.structure.planet_id != None:
		c.send("Already landed on a planet.")
		return
	elif c.structure.dock_parent != None or len(c.structure.dock_children) > 0:
		c.send("Cannot land while docked.")
		return
	report = production.update(c.structure)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send("Antigravity engines are needed to land on planets.")
		else:
			c.send("Antigravity engines are not powerful enough to land.")
		return
	c.structure.planet_id = pid
	conn.execute("UPDATE structures SET planet_id = ? WHERE id = ?;", (pid, c.structure.id))
	conn.commit()
	c.send("Landed on planet %d.", (pid,))

def handle_launch(c: Client, args: List[str]) -> None:
	s = c.structure
	if s.type != "ship":
		c.send("Only ships can be launched from a planet.")
		return
	elif s.planet_id == None:
		c.send("Not landed on a planet.")
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send("Cannot launch while docked.")
		return
	report = production.update(s)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send("Antigravity engines are needed to land on planets.")
		else:
			c.send("Antigravity engines are not powerful enough to land.")
		return
	s.planet_id = None
	conn.execute("UPDATE structures SET planet_id = NULL WHERE id = ?;", (s.id,))
	conn.commit()
	c.send("Launched from planet.")

def handle_jump(c: Client, args: List[str]) -> None:
	
	# Validate input
	s = c.structure
	if len(args) < 1:
		c.send("Usage: jump <link ID> [structure IDs]")
		return
	elif s.planet_id != None:
		c.send("Cannot engage warp engines in atmosphere.")
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send("Cannot engage warp engines while docked.")
		return
	sids = []
	try:
		lindex = int(args.pop(0))
		for arg in args:
			sids.append(int(arg))
	except ValueError:
		c.send("Not a number.")
		return
	links = s.system.get_links()
	if lindex >= len(links):
		c.send("System does not exist.")
		return
	report = production.update(s)
	if s.warp_charge < report.mass:
		c.send("Warp engines are not fully charged.")
		return
	
	# Make sure all ships are ready to jump
	ships = {s: report.mass}
	for sid in sids:
		fship = structure.load_structure(sid)
		if fship == None or fship.system.id != s.system.id:
			c.send("Unable to locate structure '%d'.", (sid,))
			return
		elif conn.execute("SELECT id FROM users WHERE structure_id = ?;", (sid,)).fetchone() != None:
			c.send("Permission denied (%d %s).", (sid, fship.name))
			return
		elif not faction.has_permission(c, fship, faction.JUMP_MIN):
			c.send("Permission denied (%d %s).", (sid, fship.name))
			return
		freport = production.update(fship)
		if fship.warp_charge < freport.mass:
			c.send("Warp engines on '%d %s' are not fully charged.", (sid, fship.name))
			return
		ships[fship] = report.mass
	
	# Perform jump
	xo, yo, drag = links[lindex]
	sys = system.System(system.to_system_id(s.system.x + xo, s.system.y + yo))
	for ship, mass in ships.items():
		cost = report.mass / pow(2, system.DRAG_BITS) * drag
		ship.system = sys
		ship.warp_charge-= cost
		conn.execute("UPDATE structures SET sys_id = ?, warp_charge = ? WHERE id = ?", (sys.id, ship.warp_charge, ship.id))
	c.send("Warp engines engaging.")
	conn.commit()
	combat.clear_targets(s)
	combat.update_targets(sys.id)
	c.send("Jump complete! Remaining charge: %d%%.", (s.warp_charge / report.mass * 100))


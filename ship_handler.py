from typing import List

import production
import system
import database
import structure
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
		c.send("Target has no available docking ports.")
	elif target.owner_id != c.id:
		c.send("Permission denied.")
	else:
		target.dock_children.append(s)
		s.dock_parent = target
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (sid, s.id))
		conn.commit()
		c.send("Docked to structure '%d %s'.", (sid, target.name))

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
	s.dock_parent.dock_children.remove(s)
	s.dock_parent = None
	conn.execute("UPDATE structures SET planet_id = NULL, dock_id = NULL WHERE id = ?;", (s.id,))
	for ship in s.dock_children:
		ship.dock_parent = None
	conn.execute("UPDATE structures SET dock_id = NULL WHERE dock_id = ?;", (s.id,))
	conn.commit()
	c.send("Launched from planets and docked structures.")

def handle_jump(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send("Usage: jump <link ID>")
		return
	elif s.planet_id != None:
		c.send("Cannot engage warp engines in atmosphere.")
		return
	elif s.dock_parent != None or len(s.dock_children) > 0:
		c.send("Cannot engage warp engines while docked.")
		return
	try:
		lindex = int(args[0])
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
	
	xo, yo, drag = links[lindex]
	cost = report.mass / pow(2, system.DRAG_BITS) * drag
	sys = system.System(system.to_system_id(s.system.x + xo, s.system.y + yo))
	c.send("Warp engines engaging, destination: %s.", (sys.name,))
	s.system = sys
	s.warp_charge-= cost
	conn.execute("UPDATE structures SET sys_id = ?, warp_charge = ? WHERE id = ?", (sys.id, s.warp_charge, s.id))
	conn.commit()
	c.send("Jump complete! Remaining charge: %d%%.", (s.warp_charge / report.mass * 100))


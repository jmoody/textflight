from typing import List

import production
import system
import database
from client import Client

conn = database.conn

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
	elif c.structure.dock_parent != None:
		c.send("Cannot land while docked to a structure.")
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

def handle_launch(c: Client) -> None:
	if c.structure.type == "base":
		c.send("Cannot launch a planetary base.")
		return
	report = production.update(c.structure)
	if report.mass > report.antigravity:
		if report.antigravity == 0:
			c.send("Antigravity engines are needed to land on planets.")
		else:
			c.send("Antigravity engines are not powerful enough to land.")
		return
	c.structure.planet_id = None
	c.structure.dock_parent = None
	conn.execute("UPDATE structures SET planet_id = NULL, dock_id = NULL WHERE id = ?;", (c.structure.id,))
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
	elif s.dock_parent != None:
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


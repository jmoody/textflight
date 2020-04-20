from typing import List

import production
import system
import database
from client import Client

conn = database.conn

def handle_jump(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) != 1:
		c.send("Usage: jump [link]")
		return
	elif s.planet_id != None:
		c.send("Cannot engage warp engines in atmosphere.")
		return
	elif s.dock_parent != None:
		c.send("Cannot engage warp engines while docked.")
		return
	try:
		lindex = int(args[0])
	except:
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


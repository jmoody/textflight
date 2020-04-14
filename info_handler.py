from typing import List

import database
import system
import structure
import production
from client import Client

conn = database.conn

def handle_nav(c: Client) -> None:
	sys = c.structure.system
	c.send("System: %s", (sys.name,))
	c.send("Brightness: %s", (sys.brightness,))
	c.send("Asteroids: %s (density: %d)", (c.translate(sys.asteroid_type.name.lower()), sys.asteroid_richness))
	c.send("Links:")
	for link in sys.get_links():
		xo, yo, drag = link
		sys = system.System(system.to_system_id(sys.x + xo, sys.y + yo))
		c.send("	%s (drag: %d)", (sys.name, drag))
	c.send("Planets:")
	for planet in sys.planets:
		c.send("	%s (%s)", (planet.name, c.translate(planet.ptype.name.lower())))
	c.send("Structures:")
	for stup in conn.execute("SELECT id, name FROM structures WHERE sys_id = ?;", (c.structure.system.id,)):
		sid, name = stup
		c.send("	%d %s", (sid, name))

def handle_rename(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send("Usage: rename <name>")
		return
	name = " ".join(args)
	c.send("Renamed '%s' to '%s'.", (c.structure.name, name))
	c.structure.rename(name)

def handle_scan(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) == 1:
		s = structure.load_structure(args[0])
		if s == None:
			c.send("Unable to locate structure.")
			return
		elif s.system.id != c.structure.system.id:
			c.send("Unable to locate structure.")
			return
	elif len(args) > 1:
		c.send("Usage: scan [target ID]")
		return
	production.update(s)
	c.send("Callsign: %d %s", (s.id, s.name))
	if s.planet_id != None:
		c.send("Landed on %s", (s.system.planets[0].name,))
	if s.dock_id != None:
		dock_name = conn.execute("SELECT name FROM structures WHERE id = ?", (s.dock_id,)).fetchone()[0]
		c.send("Docked to %d %s", (s.dock_id, dock_name))
	c.send("Outfit space: %d", (s.outfit_space,))
	c.send("Heat: %d", (s.heat,))
	c.send("Energy: %d", (s.energy,))
	c.send("Shield charge: %d", (s.shield,))
	c.send("Warp charge: %d", (s.warp_charge,))
	c.send("Outfits:")
	index = 0
	for out in s.outfits:
		c.send("	[%d] %s mark %d (setting %d)", (index, c.translate(out.type), out.mark, out.setting))
		index+= 1
	c.send("Cargo:")
	index = 0
	for car in s.cargo:
		if car.extra != None:
			c.send("	[%d] %s (%s) x%d", (index, c.translate(car.type), car.extra, car.count))
		else:
			c.send("	[%d] %s x%d", (index, c.translate(car.type), car.count))
		index+= 1

def handle_status(c: Client) -> None:
	s = c.structure
	report = production.update(s)
	if report.overheat_time == None:
		c.send("Cooling status: Stable.")
	elif report.overheat_time > report.now:
		c.send("Cooling status: Overheat in %d seconds!" % (report.overheat_time - report.now,))
	else:
		c.send("Cooling status: OVERHEATED!")
	c.send("Net heat generation: %d/s.", (report.heat_rate,))
	if report.powerloss_time == None:
		c.send("Power status: Stable.")
	elif report.powerloss_time > report.now:
		c.send("Power status: System failure in %d seconds!" % (report.powerloss_time - report.now,))
	else:
		c.send("Power status: SYSTEM FAILURE!")
	c.send("Net power consumption: %d/s.", (report.energy_rate,))
	if report.mining_interval > 0:
		c.send("Mining beam power: %d.", (report.mining_power,))
		progress = s.mining_progress / report.mining_interval * 100
		c.send("Mining progress: %.2f%% (%.2f second interval).", (progress, report.mining_interval))


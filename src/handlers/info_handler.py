import logging
from typing import List

import database
import system
import structure
import production
import faction
import territory
from client import Client

conn = database.conn

def handle_nav(c: Client, args: List[str]) -> None:
	sys = c.structure.system
	fid, name = territory.get_system(sys)
	if name != None:
		c.send("System: %s", (name,))
	if fid != None:
		fact = faction.get_faction(fid)
		c.send("Claimed by '%s'.", (fact.name,))
	c.send("Brightness: %s", (sys.brightness,))
	c.send("Asteroids: %s (density: %d)", (c.translate(sys.asteroid_type.name.lower()), sys.asteroid_richness))
	c.send("Links:")
	index = 0
	for link in sys.get_links():
		lid, drag, xo, yo = link
		direction = ""
		if yo < 0:
			direction = "north"
		elif yo > 0:
			direction = "south"
		if xo < 0:
			direction+= "west"
		elif xo > 0:
			direction+= "east"
		target_sys = system.System(lid)
		tfid, tname = territory.get_system(target_sys)
		if tname != None:
			tfact = faction.get_faction(tfid)
			c.send("	[%d] %s (faction: %s) (%s) (drag: %d)", (index, tname, tfact.name, c.translate(direction), drag))
		elif tfid != None:
			tfact = faction.get_faction(tfid)
			c.send("	[%d] (faction: %s) (%s) (drag: %d)", (index, tfact.name, c.translate(direction), drag))
		else:
			c.send("	[%d] (%s) (drag: %d)", (index, c.translate(direction), drag))
		index+= 1
	c.send("Planets:")
	index = 0
	for planet in sys.planets:
		pfid, pname = territory.get_planet(sys, index)
		if pname != None:
			pfact = faction.get_faction(pfid)
			c.send("	[%d] %s (faction: %s) (%s)", (index, pname, pfact.name, c.translate(planet.ptype.name.lower())))
		elif pfid != None:
			pfact = faction.get_faction(pfid)
			c.send("	[%d] (faction: %s) (%s)", (index, pfact.name, c.translate(planet.ptype.name.lower())))
		else:
			c.send("	[%d] (%s)", (index, c.translate(planet.ptype.name.lower())))
		index+= 1
	c.send("Structures:")
	for stup in conn.execute("SELECT id, name FROM structures WHERE sys_id = ?;", (c.structure.system.id_db,)):
		sid, name = stup
		c.send("	%d %s.", (sid, name))

def handle_scan(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send("Not a number.")
			return
		s = structure.load_structure(sid)
		if s == None:
			c.send("Unable to locate structure.")
			return
		elif s.system.id != c.structure.system.id:
			c.send("Unable to locate structure.")
			return
	elif len(args) > 1:
		c.send("Usage: scan [structure ID]")
		return
	production.update(s)
	c.send("Callsign: %d %s", (s.id, s.name))
	utup = conn.execute("SELECT username, faction_id, structure_id FROM users WHERE id = ?;", (s.owner_id,)).fetchone()
	fact = faction.get_faction(utup["faction_id"])
	if fact.name == "":
		c.send("Owner: %s", (utup["username"],))
	else:
		c.send("Owner: %s (%s)", (utup["username"], fact.name))
	wrote_pilots = False
	for uname in conn.execute("SELECT username FROM users WHERE structure_id = ?;", (s.id,)):
		if not wrote_pilots:
			wrote_pilots = True
			c.send("Operators:")
		c.send("	%s", (uname["username"],))
	if s.planet_id != None:
		c.send("Landed on planet %d.", (s.planet_id,))
	if s.dock_parent != None:
		c.send("Docked to '%d %s'.", (s.dock_parent.id, s.dock_parent.name))
	elif len(s.dock_children) > 0:
		c.send("Docked structures:")
		for sdock in s.dock_children:
			c.send("	%d %s", (sdock.id, sdock.name))
	c.send("Outfit space: %d", (s.outfit_space,))
	c.send("Shield charge: %d", (s.shield,))
	c.send("Outfits:")
	index = 0
	for out in s.outfits:
		c.send("	[%d] %s mark %d (setting %d)", (index, c.translate(out.type.name), out.mark, out.setting))
		index+= 1
	c.send("Cargo:")
	index = 0
	for car in s.cargo:
		if car.extra != None:
			c.send("	[%d] %s (%s) x%d", (index, c.translate(car.type), car.extra, car.count))
		else:
			c.send("	[%d] %s x%d", (index, c.translate(car.type), car.count))
		index+= 1

def handle_status(c: Client, args: List[str]) -> None:
	s = c.structure
	report = production.update(s)
	
	# Heat and energy management
	c.send("General:")
	c.send("	Mass: %d", (report.mass,))
	c.send("	Outfit space: %d/%d", (report.outfit_space, s.outfit_space))
	c.send("	Heat: %d/%d", (s.heat, report.max_heat))
	c.send("	Energy: %d/%d", (s.energy, report.max_energy))
	c.send("Stability:")
	if report.overheat_time == None:
		c.send("	Cooling status: Stable")
	elif report.overheat_time > report.now:
		c.send("	Cooling status: Overheat in %d seconds!" % (report.overheat_time - report.now,))
	else:
		c.send("	Cooling status: OVERHEATED")
	c.send("	Net heat generation: %.1f/s", (report.heat_rate,))
	if report.powerloss_time == None:
		c.send("	Power status: Stable")
	elif report.powerloss_time > report.now:
		c.send("	Power status: Brownout in %d seconds!" % (report.powerloss_time - report.now,))
	else:
		c.send("	Power status: BROWNOUT")
	c.send("	Net energy consumption: %.1f/s", (report.energy_rate,))
	
	# Generators
	if len(report.generators) > 0:
		c.send("Reactors:")
	for outfit, fuelout in report.generators.items():
		if fuelout > report.now:
			c.send("	[%d] %s mark %d: %d seconds of fuel remaining.", (s.outfits.index(outfit), c.translate(outfit.type.name), outfit.mark, fuelout - report.now))
		else:
			c.send("	[%d] %s mark %d: OUT OF FUEL", (s.outfits.index(outfit), c.translate(outfit.type.name), outfit.mark))
	
	# Extra systems
	if report.has_shields:
		if s.shield == report.max_shield:
			c.send("Shields: Online")
		elif report.shield_rate > 0:
			c.send("Shields: Regenerating (%d/%d)", (s.shield, report.max_shield))
		elif s.shield > 0:
			c.send("Shields: Offline (%d/%d)", (s.shield, report.max_shield))
		else:
			c.send("Shields: FAILED")
	if report.normal_warp > 0:
		if s.warp_charge == report.mass:
			c.send("Warp engines: Ready to engage")
		elif report.warp_rate > 0:
			c.send("Warp engines: Charging (%d%%)", s.warp_charge / report.mass * 100)
		else:
			c.send("Warp engines: Offline")
	if report.antigravity > 0:
		if report.mass > report.antigravity:
			c.send("Antigravity engines: OVERLOADED")
		else:
			c.send("Antigravity engines: Online")
	if report.mining_interval > 0:
		progress = s.mining_progress / report.mining_interval * 100
		c.send("Mining progress: %.1f%% (%.1f second interval)", (progress, report.mining_interval))


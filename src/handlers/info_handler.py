import logging
from typing import List
from enum import Enum

import database
import system
import structure
import production
import faction
import territory
import strings
from client import Client

conn = database.conn

class ShipClass(Enum):
	JUNK = "JNK"
	SATELLITE = "SAT"
	METEOR = "MET"
	ASTEROID = "AST"
	LUNAR = "LUN"
	PLANETARY = "PLA"
	GIANT = "GIA"
	DWARF = "DWA"
	STELLAR = "STE"
	NEBULA = "NEB"
	GALAXY = "GAL"

def handle_nav(c: Client, args: List[str]) -> None:
	sys = c.structure.system
	remote = False
	if len(args) == 2:
		try:
			x = int(args[0])
			y = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		sys = system.System(system.to_system_id(sys.x + x, sys.y + y))
		rows = conn.execute("SELECT * FROM map WHERE user_id = ? AND sys_id = ?;", (c.id, sys.id_db))
		if len(rows.fetchall()) == 0:
			c.send(strings.INFO.NOT_DISCOVERED)
			return
		remote = True
	elif len(args) != 0:
		c.send(strings.USAGE.NAV)
		return
	cx = sys.x
	cy = sys.y
	if cx > pow(2, 31):
		cx-= 1 << 32
	if cy > pow(2, 31):
		cy-= 1 << 32
	c.send(strings.INFO.COORDS, x=cx, y=cy)
	fid, name = territory.get_system(sys)
	if name != None:
		c.send(strings.INFO.SYSTEM, name=name)
	if fid != None:
		fact = faction.get_faction(fid)
		c.send(strings.INFO.CLAIMED_BY, faction=fact.name)
	c.send(strings.INFO.BRIGHTNESS, brightness=sys.brightness)
	c.send(strings.INFO.ASTEROIDS, asteroid_type=c.translate(sys.asteroid_type.name.lower()), asteroid_density=sys.asteroid_richness)
	c.send(strings.INFO.LINKS)
	index = 0
	for link in sys.get_links():
		lid, drag, xo, yo = link
		if yo == -1:
			if xo == -1:
				direction = strings.INFO.NORTHWEST
			elif xo == 1:
				direction = strings.INFO.NORTHEAST
			else:
				direction = strings.INFO.NORTH
		elif yo == 1:
			if xo == -1:
				direction = strings.INFO.SOUTHWEST
			elif xo == 1:
				direction = strings.INFO.SOUTHEAST
			else:
				direction = strings.INFO.SOUTH
		elif xo == -1:
			direction = strings.INFO.WEST
		else:
			direction = strings.INFO.EAST
		target_sys = system.System(lid)
		tfid, tname = territory.get_system(target_sys)
		if tname != None:
			tfact = faction.get_faction(tfid)
			c.send(strings.INFO.LINK_NAMED, index=index, name=tname, faction=tfact.name, direction=c.translate(direction), link_drag=drag)
		elif tfid != None:
			tfact = faction.get_faction(tfid)
			c.send(strings.INFO.LINK_CLAIMED, index=index, faction=tfact.name, direction=c.translate(direction), link_drag=drag)
		else:
			c.send(strings.INFO.LINK, index=index, direction=c.translate(direction), link_drag=drag)
		index+= 1
	c.send(strings.INFO.PLANETS)
	index = 0
	for planet in sys.planets:
		pfid, pname = territory.get_planet(sys, index)
		if pname != None:
			pfact = faction.get_faction(pfid)
			c.send(strings.INFO.PLANET_NAMED, index=index, name=pname, faction=pfact.name, planet_type=c.translate(planet.ptype.name.lower().capitalize()))
		elif pfid != None:
			pfact = faction.get_faction(pfid)
			c.send(strings.INFO.PLANET_CLAIMED, index=index, faction=pfact.name, planet_type=c.translate(planet.ptype.name.lower().capitalize()))
		else:
			c.send(strings.INFO.PLANET, index=index, planet_type=c.translate(planet.ptype.name))
		index+= 1
	if not remote:
		c.send(strings.INFO.STRUCTURES)
		for stup in conn.execute("SELECT id, name, type, outfit_space FROM structures WHERE sys_id = ?;", (c.structure.system.id_db,)):
			sid, name, stype, os = stup
			if stype == "ship":
				sclass = ShipClass.JUNK
				if os >= 1024:
					sclass = ShipClass.GALAXY
				elif os >= 512:
					sclass = ShipClass.NEBULA
				elif os >= 256:
					sclass = ShipClass.STELLAR
				elif os >= 128:
					sclass = ShipClass.DWARF
				elif os >= 64:
					sclass = ShipClass.GIANT
				elif os >= 32:
					sclass = ShipClass.PLANETARY
				elif os >= 16:
					sclass = ShipClass.LUNAR
				elif os >= 8:
					sclass = ShipClass.ASTEROID
				elif os >= 4:
					sclass = ShipClass.METEOR
				elif os >= 2:
					sclass = ShipClass.SATELLITE
				c.send(strings.INFO.SHIP, id=sid, name=name, sclass=sclass.value)
			else:
				c.send(strings.INFO.STRUCTURE, id=sid, name=name)

def handle_scan(c: Client, args: List[str]) -> None:
	s = c.structure
	if len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		s = structure.load_structure(sid)
		if s == None or s.system.id != c.structure.system.id:
			c.send(strings.MISC.NO_STRUCT)
			return
	elif len(args) > 1:
		c.send(strings.USAGE.SCAN)
		return
	production.update(s)
	c.send(strings.INFO.CALLSIGN, id=s.id, name=s.name)
	utup = conn.execute("SELECT username, faction_id, structure_id FROM users WHERE id = ?;", (s.owner_id,)).fetchone()
	fact = faction.get_faction(utup["faction_id"])
	if fact.name == "":
		c.send(strings.INFO.OWNER, username=utup["username"])
	else:
		c.send(strings.INFO.OWNER_FACTION, username=utup["username"], faction=fact.name)
	wrote_pilots = False
	for uname in conn.execute("SELECT username FROM users WHERE structure_id = ?;", (s.id,)):
		if not wrote_pilots:
			wrote_pilots = True
			c.send(strings.INFO.OPERATORS)
		c.send(strings.INFO.OPERATOR, username=uname["username"])
	if s.planet_id != None:
		c.send(strings.INFO.LANDED, planet_id=s.planet_id)
	if s.dock_parent != None:
		c.send(strings.INFO.DOCKED_TO, id=s.dock_parent.id, name=s.dock_parent.name)
	elif len(s.dock_children) > 0:
		c.send(strings.INFO.DOCKED)
		for sdock in s.dock_children:
			c.send(strings.INFO.DOCK, id=sdock.id, name=sdock.name)
	c.send(strings.INFO.OUTFIT_SPACE_TOTAL, space=s.outfit_space)
	c.send(strings.INFO.SHIELD_CHARGE, charge=s.shield)
	c.send(strings.INFO.OUTFITS)
	index = 0
	for out in s.outfits:
		c.send(strings.INFO.OUTFIT, index=index, name=c.translate(out.type.name), mark=out.mark, setting=out.setting)
		index+= 1
	c.send(strings.INFO.CARGOS)
	index = 0
	for car in s.cargo:
		if car.extra != None:
			c.send(strings.INFO.CARGO_EXTRA, index=index, name=c.translate(car.type), extra=car.extra, count=car.count)
		else:
			c.send(strings.INFO.CARGO, index=index, name=c.translate(car.type), count=car.count)
		index+= 1

def handle_status(c: Client, args: List[str]) -> None:
	s = c.structure
	report = production.update(s, send_updates=True)
	
	# Heat and energy management
	c.send(strings.INFO.GENERAL)
	c.send(strings.INFO.MASS, mass=report.mass)
	c.send(strings.INFO.OUTFIT_SPACE, space=report.outfit_space, total=s.outfit_space)
	c.send(strings.INFO.HEAT, heat=round(s.heat), max=report.max_heat)
	c.send(strings.INFO.ENERGY, energy=round(s.energy), max=report.max_energy)
	c.send(strings.INFO.STABILITY)
	if report.overheat_time == None:
		c.send(strings.INFO.COOLING_STATUS_STABLE)
	elif report.overheat_time > report.now:
		c.send(strings.INFO.COOLING_STATUS_OVERHEAT_IN, remaining=round(report.overheat_time - report.now))
	else:
		c.send(strings.INFO.COOLING_STATUS_OVERHEAT)
	c.send(strings.INFO.NET_HEAT, heat_rate="%.1f" % (report.heat_rate,))
	if report.powerloss_time == None:
		c.send(strings.INFO.POWER_STATUS_STABLE)
	elif report.powerloss_time > report.now:
		c.send(strings.INFO.POWER_STATUS_BROWNOUT_IN, remaining=round(report.powerloss_time - report.now))
	else:
		c.send(strings.INFO.POWER_STATUS_BROWNOUT)
	c.send(strings.INFO.NET_ENERGY, energy_rate="%.1f" % (report.energy_rate,))
	
	# Generators
	if len(report.generators) > 0:
		c.send(strings.INFO.REACTORS)
	for outfit, fuelout in report.generators.items():
		if fuelout > report.now:
			c.send(strings.INFO.REACTOR, index=s.outfits.index(outfit), name=c.translate(outfit.type.name), mark=outfit.mark, remaining=round(fuelout - report.now))
		else:
			c.send(strings.INFO.REACTOR_NOFUEL, index=s.outfits.index(outfit), name=c.translate(outfit.type.name), mark=outfit.mark)
	
	# Extra systems
	if report.has_shields:
		if s.shield == report.max_shield:
			c.send(strings.INFO.SHIELDS_ONLINE)
		elif report.shield_rate != 0:
			c.send(strings.INFO.SHIELDS_REGENERATING, shield=round(s.shield), max=report.max_shield, rate="%.1f" % report.shield_rate)
		elif s.shield > 0:
			c.send(strings.INFO.SHIELDS_OFFLINE, shield=round(s.shield), max=report.max_shield)
		else:
			c.send(strings.INFO.SHIELDS_FAILED)
	if report.normal_warp > 0:
		if s.warp_charge == report.mass:
			c.send(strings.INFO.WARP_READY)
		elif report.warp_rate > 0:
			c.send(strings.INFO.WARP_CHARGING, charge=round(s.warp_charge / report.mass * 100))
		else:
			c.send(strings.INFO.WARP_OFFLINE)
	if report.antigravity > 0:
		if report.mass > report.antigravity:
			c.send(strings.INFO.ANTIGRAVITY_OVERLOADED)
		else:
			c.send(strings.INFO.ANTIGRAVITY_ONLINE)
	if report.crew > 0:
		c.send(strings.INFO.CREW, crew=int(report.crew))
	if report.mining_interval > 0:
		progress = s.mining_progress / report.mining_interval * 100
		c.send(strings.INFO.MINING_PROGRESS, progress=round(progress), interval="%.1f" % (report.mining_interval,))


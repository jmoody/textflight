import time
import logging
import math
from typing import List

import crafting
import production
import structure
import database
import system
import strings
import config
from cargo import Cargo
from client import Client
from system import PlanetType

crft = config.get_section("crafting")
MAX_OUTFIT_SPACE = crft.getint("MaxOutfitSpace")
MAX_PLANET_SPACE = crft.getint("MaxPlanetSpace")
MAX_HABITABLE_SPACE = crft.getint("MaxHabitableSpace")

conn = database.conn

def handle_base(c: Client, args: List[str]) -> None:
	handle_construct(c, args, True)

def handle_cancel(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send(strings.USAGE.CANCEL)
		return
	try:
		qindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if count < 1:
		c.send(strings.MISC.COUNT_GTZ)
	elif qindex >= len(c.structure.craft_queue):
		c.send(strings.CRAFT.NO_QUEUE)
	else:
		c.structure.craft_queue[qindex].less(count, c.structure)
		c.send(strings.CRAFT.CANCELLED, count=count)
		production.update(c.structure, send_updates=True)

def handle_construct(c: Client, args: List[str], base = False) -> None:
	
	# Validate input
	if len(args) < 2:
		if base:
			c.send(strings.USAGE.BASE)
		else:
			c.send(strings.USAGE.CONSTRUCT)
		return
	try:
		outfit_space = int(args.pop(0))
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if outfit_space < 1:
		c.send(strings.CRAFT.OUTFIT_SPACE_GTZ)
		return
	elif not base and outfit_space > MAX_OUTFIT_SPACE:
		c.send(strings.CRAFT.OUTFIT_SPACE_LT, max=MAX_OUTFIT_SPACE)
		return
	s = c.structure
	report = production.update(s)
	name = " ".join(args)
	if base:
		pmax = MAX_PLANET_SPACE
		if s.planet_id == None or s.system.planets[s.planet_id].ptype == system.PlanetType.GAS:
			c.send(strings.CRAFT.NEED_ROCKY)
			return
		elif s.system.planets[s.planet_id].ptype == system.PlanetType.HABITABLE:
			pmax = MAX_HABITABLE_SPACE
		total = outfit_space
		for pbase in conn.execute("SELECT outfit_space FROM structures WHERE type = 'base' AND sys_id = ? AND planet_id = ?", (s.system.id_db, s.planet_id)):
			total+= pbase["outfit_space"]
		if total > pmax:
			c.send(strings.CRAFT.TOTAL_SPACE_LT, max=pmax)
			return
	elif outfit_space > report.shipyard:
		if report.shipyard == 0:
			c.send(strings.CRAFT.NEED_SHIPYARD)
		else:
			c.send(strings.CRAFT.SMALL_SHIPYARD)
		return
	
	# Determine the cost
	if not base:
		cost_factor = crafting.COST_FACTOR_SHIP
	elif s.system.planets[s.planet_id].ptype == PlanetType.HABITABLE:
		cost_factor = crafting.COST_FACTOR_HABITABLE
	else:
		cost_factor = crafting.COST_FACTOR_PLANET
	cost = math.ceil(pow(outfit_space, cost_factor))
	
	# Remove the materials
	has_struct = False
	has_plating = False
	for cargo in s.cargo:
		if cargo.type == "Light Material":
			has_struct = cargo.count >= cost
			if not has_struct:
				break
		elif cargo.type == "Heavy Plating":
			has_plating = cargo.count >= outfit_space
			if not has_plating:
				break
	if not has_struct:
		c.send(strings.CRAFT.INSUFFICIENT, material=c.translate("Light Material"), count=cost)
		return
	if not has_plating:
		c.send(strings.CRAFT.INSUFFICIENT, material=c.translate("Heavy Plating"), count=outfit_space)
		return
	Cargo("Light Material", cost).remove(s)
	Cargo("Heavy Plating", outfit_space).remove(s)
	
	# Create the structure
	if base:
		struct = structure.create_structure(name, c.id, "base", outfit_space, s.system, s.planet_id)
	else:
		struct = structure.create_structure(name, c.id, "ship", outfit_space, s.system, s.planet_id)
	logging.info("Structure '%d %s' created by %d.", struct.id, name, c.id)
	c.send(strings.CRAFT.CREATED_STRUCT, name=name, size=outfit_space)
	production.update(c.structure, send_updates=True)

def handle_craft(c: Client, args: List[str]) -> None:
	report = production.update(c.structure)
	available = crafting.list_available(c.structure)
	if len(args) < 1:
		for rid, q in available.items():
			c.send(strings.CRAFT.RECIPE, index=rid, name=c.translate(q.type), count=q.count)
	elif 1 < len(args) < 4:
		if report.assembly_rate == 0:
			c.send(strings.CRAFT.NO_ASSEMBLERS)
			return
		
		# Validate input
		try:
			index = int(args[0])
			count = int(args[1])
			extra = 0
			if len(args) > 2:
				extra = int(args[2])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		if count < 1:
			c.send(strings.MISC.COUNT_GTZ)
			return
		elif not index in available:
			c.send(strings.CRAFT.NO_RECIPE)
			return
		q = available[index]
		if q.count < count * max(1, extra):
			c.send(strings.CRAFT.INSUFFICIENTS)
			return
		elif extra < 1 and q._rec.has_extra:
			c.send(strings.CRAFT.MISSING_MARK)
			return
		elif extra != 0 and not q._rec.has_extra:
			c.send(strings.CRAFT.NO_MARK)
			return
		
		# Remove cargo and add to queue
		for ctype in q._rec.inputs:
			Cargo(ctype, count * max(1, extra) * q._rec.inputs[ctype]).remove(c.structure)
		q.count = count
		if extra > 0:
			q.extra = extra
		q.add(c.structure)
		c.send(strings.CRAFT.QUEUED, count=count)
		production.update(c.structure, send_updates=True)
		
	else:
		c.send(strings.USAGE.CRAFT)

def handle_expand(c: Client, args: List[str]) -> None:
	
	# Validate input
	s = c.structure
	if len(args) != 1:
		c.send(strings.USAGE.EXPAND)
		return
	try:
		count = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if count < 1:
		c.send(strings.CRAFT.OUTFIT_SPACE_GTZ)
		return
	elif s.type != "base":
		c.send(strings.CRAFT.NOT_BASE)
		return
	outfit_space = s.outfit_space + count
	
	# Check max outfit space
	pmax = MAX_PLANET_SPACE
	if s.system.planets[s.planet_id].ptype == system.PlanetType.HABITABLE:
		pmax = MAX_HABITABLE_SPACE
	total = outfit_space
	for pbase in conn.execute("SELECT outfit_space FROM structures WHERE type = 'base' AND sys_id = ? AND planet_id = ?", (s.system.id_db, s.planet_id)):
		total+= pbase["outfit_space"]
	if total > pmax:
		c.send(strings.CRAFT.TOTAL_SPACE_LT, max=pmax)
		return
	
	# Determine the cost
	if s.system.planets[s.planet_id].ptype == PlanetType.HABITABLE:
		cost_factor = crafting.COST_FACTOR_HABITABLE
	else:
		cost_factor = crafting.COST_FACTOR_PLANET
	cost = math.ceil(pow(outfit_space, cost_factor)) - math.ceil(pow(s.outfit_space, cost_factor))
	
	# Remove the materials
	has_struct = False
	has_plating = False
	for cargo in s.cargo:
		if cargo.type == "Light Material":
			has_struct = cargo.count >= cost
			if not has_struct:
				break
		elif cargo.type == "Heavy Plating":
			has_plating = cargo.count >= outfit_space
			if not has_plating:
				break
	if not has_struct:
		c.send(strings.CRAFT.INSUFFICIENT, material=c.translate("Light Material"), count=cost)
	if not has_plating:
		c.send(strings.CRAFT.INSUFFICIENT, material=c.translate("Heavy Plating"), count=outfit_space)
	if not has_struct or not has_plating:
		return
	Cargo("Light Material", cost).remove(s)
	Cargo("Heavy Plating", outfit_space).remove(s)
	
	# Increase outfit space
	s.outfit_space = outfit_space
	conn.execute("UPDATE structures SET outfit_space = ? WHERE id = ?;", (outfit_space, s.id))
	conn.commit()
	c.send(strings.CRAFT.EXPANDED, id=s.id, name=s.name, size=outfit_space)
	production.update(c.structure, send_updates=True)

def handle_jettison(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send(strings.USAGE.JETTISON)
		return
	try:
		cindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if count < 0:
		c.send(strings.MISC.COUNT_GTZ)
	elif cindex >= len(c.structure.cargo):
		c.send(strings.MISC.NO_CARGO)
	else:
		if count == 0:
			count = c.structure.cargo[cindex].count
		count = min(c.structure.cargo[cindex].count, count)
		c.structure.cargo[cindex].less(count, c.structure)
		c.send(strings.CRAFT.JETTISONED, count=count)
	production.update(c.structure, send_updates=True)

def handle_queue(c: Client, args: List[str]) -> None:
	i = 0
	report = production.update(c.structure)
	for q in c.structure.craft_queue:
		if report.assembly_rate > 0:
			craft_time = crafting.craft_time(q)
			ntime = q.work / report.assembly_rate
			ftime = (q.work + craft_time * q.count) / report.assembly_rate
			time_str = "%ds/%ds" % (ntime, ftime)
		else:
			time_str = "never"
		if q.extra == None:
			c.send(strings.CRAFT.QUEUE, index=i, name=c.translate(q.type), count=q.count + 1, time=time_str)
		else:
			c.send(strings.CRAFT.QUEUE_EXTRA, index=i, name=c.translate(q.type), extra=q.extra, count=q.count + 1, time=time_str)
		i+= 1


import time
import logging
from typing import List

import crafting
import production
import structure
import database
from cargo import Cargo
from client import Client
from system import PlanetType

conn = database.conn

def handle_base(c: Client, args: List[str]) -> None:
	handle_construct(c, args, True)

def handle_cancel(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send("Usage: cancel <queue ID> <count>")
		return
	try:
		qindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if count < 1:
		c.send("Count must be greater than zero.")
	elif qindex >= len(c.structure.craft_queue):
		c.send("Queue does not exist.")
	else:
		c.structure.craft_queue[qindex].less(count, c.structure)
		c.send("Cancelled %d items queued for assembly.", (count,))

def handle_construct(c: Client, args: List[str], base = False) -> None:
	
	# Validate input
	if len(args) < 2:
		if base:
			c.send("Usage: base <outfit space> <name>")
		else:
			c.send("Usage: construct <outfit space> <name>")
		return
	try:
		outfit_space = int(args.pop(0))
	except ValueError:
		c.send("Not a number.")
		return
	if outfit_space < 1:
		c.send("Outfit space must be greater than zero.")
		return
	elif outfit_space > 1024:
		c.send("Outfit space must be less than 1024.")
		return
	s = c.structure
	report = production.update(s)
	name = " ".join(args)
	if base:
		if s.planet_id == None:
			c.send("Must be landed on a planet to construct a base.")
			return
		total = outfit_space
		for pbase in conn.execute("SELECT outfit_space FROM structures WHERE type = 'base' AND sys_id = ? AND planet_id = ?", (s.system.id_db, s.planet_id)):
			total+= pbase["outfit_space"]
		if total > 1024:
			c.send("Total outfit space of all bases must be less than 1024.")
			return
	elif outfit_space > report.shipyard:
		if report.shipyard == 0:
			c.send("Shipyard required to construct new structures.")
		else:
			c.send("Shipyard not large enough to construct this structure.")
		return
	
	# Determine the cost
	if not base:
		cost_factor = crafting.COST_FACTOR_SHIP
	elif s.system.planets[s.planet_id] == PlanetType.HABITABLE:
		cost_factor = crafting.COST_FACTOR_HABITABLE
	else:
		cost_factor = crafting.COST_FACTOR_PLANET
	cost = pow(outfit_space, cost_factor)
	
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
		c.send("Insufficient 'Light Material' (needs %d).", (cost,))
		return
	if not has_plating:
		c.send("Insufficient 'Heavy Plating' (needs %d).", (outfit_space,))
		return
	Cargo("Light Material", cost).remove(s)
	Cargo("Heavy Plating", outfit_space).remove(s)
	
	# Create the structure
	if base:
		struct = structure.create_structure(name, c.id, "base", outfit_space, s.system, s.planet_id)
	else:
		struct = structure.create_structure(name, c.id, "ship", outfit_space, s.system, s.planet_id, s.id)
	logging.info("Structure '%d %s' created by %d.", struct.id, name, c.id)
	c.send("Successfully created structure '%s' with size %d.", (name, outfit_space))

def handle_craft(c: Client, args: List[str]) -> None:
	production.update(c.structure)
	available = crafting.list_available(c.structure)
	if len(args) < 1:
		i = 0
		for q in available:
			c.send("[%d] %s (x%d)", (i, c.translate(q.type), q.count))
			i+= 1
	elif 1 < len(args) < 4:
		
		# Validate input
		try:
			index = int(args[0])
			count = int(args[1])
			extra = 0
			if len(args) > 2:
				extra = int(args[2])
		except ValueError:
			c.send("Not a number.")
			return
		if count < 1:
			c.send("Count must be greater than zero.")
			return
		elif index >= len(available):
			c.send("Recipe does not exist.")
			return
		q = available[index]
		if q.count < count * max(1, extra):
			c.send("Insufficient resources.")
			return
		elif extra < 1 and q._rec.has_extra:
			c.send("Mark not specified.")
			return
		elif extra != 0 and not q._rec.has_extra:
			c.send("Recipe has no mark options.")
			return
		
		# Remove cargo and add to queue
		for ctype in q._rec.inputs:
			Cargo(ctype, count * max(1, extra) * q._rec.inputs[ctype]).remove(c.structure)
		q.count = count
		if extra > 0:
			q.extra = extra
		q.add(c.structure)
		c.send("Queued %d items for assembly.", (count,))
		
	else:
		c.send("Usage: craft [recipe ID] [count] [mark]")

def handle_jettison(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send("Usage: jettison <cargo ID> <count>")
		return
	try:
		cindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if count < 1:
		c.send("Count must be greater than zero.")
	elif cindex >= len(c.structure.cargo):
		c.send("Cargo does not exist.")
	else:
		c.structure.cargo[cindex].less(count, c.structure)
		c.send("Jettisoned %d items from cargo.", (count,))

def handle_queue(c: Client, args: List[str]) -> None:
	i = 0
	report = production.update(c.structure)
	for q in c.structure.craft_queue:
		if report.assembly_rate > 0:
			elapsed = time.time() - q.start
			craft_time = crafting.craft_time(q, report.assembly_rate)
			ntime = craft_time - elapsed
			ftime = craft_time * q.count - elapsed
			time_str = "%ds/%ds" % (ntime, ftime)
		else:
			time_str = "never"
		if q.extra == None:
			c.send("[%d] %s x%d - %s", (i, c.translate(q.type), q.count, time_str))
		else:
			c.send("[%d] %s (%s) x%d - %s", (i, c.translate(q.type), q.extra, q.count, time_str))
		i+= 1

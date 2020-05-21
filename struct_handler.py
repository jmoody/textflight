import copy
from typing import List

import outfittype
import production
import database
import faction
from client import Client
from cargo import Cargo
from outfit import Outfit

conn = database.conn

def handle_board(c: Client, args: List[str]):
	if len(args) != 1:
		c.send("Usage: board <structure ID>")
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if c.structure.dock_parent == None:
		s = None
		for struct in c.structure.dock_children:
			if struct.id == sid:
				s = struct
				break
		if s == None:
			c.send("Unable to locate docked structure.")
			return
	else:
		if c.structure.dock_parent.id != sid:
			c.send("Unable to locate docked structure.")
			return
		s = c.structure.dock_parent
	c.structure = s
	conn.execute("UPDATE users SET structure_id = ? WHERE id = ?;", (s.id, c.id))
	conn.commit()
	c.send("Boarded '%d %s'.", (sid, s.name))

def handle_eject(c: Client, args: List[str]):
	s = c.structure
	if len(args) == 0:
		if s.dock_parent == None:
			for ship in s.dock_children:
				ship.dock_parent = None
			s.dock_children = []
			conn.execute("UPDATE structures SET dock_id = NULL where dock_id = ?;", (s.id,))
			conn.commit()
			c.send("Ejected all docked structures.")
		else:
			s.dock_parent.dock_children.remove(s)
			s.dock_parent = None
			conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (s.id,))
			conn.commit()
			c.send("Ejected from docked structure.")
	elif len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send("Not a number.")
			return
		if s.dock_parent != None:
			if s.dock_parent.id == sid:
				s.dock_parent.dock_children.remove(s)
				s.dock_parent = None
				conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (s.id,))
				conn.commit()
				c.send("Ejected from docked structure.")
			else:
				c.send("Unable to locate docked structure.")
		else:
			for ship in s.dock_children:
				if ship.id == sid:
					s.dock_children.remove(ship)
					ship.dock_parent = None
					conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (ship.id,))
					c.send("Ejected '%d %s'.", (ship.id, ship.name))
					return
			c.send("Unable to locate docked structure.")
	else:
		c.send("Usage: eject [structure ID]")

def handle_install(c: Client, args: List[str]):
	if len(args) != 1:
		c.send("Usage: install <cargo ID>")
		return
	try:
		cindex = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if cindex >= len(c.structure.cargo):
		c.send("Cargo does not exist.")
	else:
		for o in c.structure.outfits:
			if o.setting != 0:
				c.send("Structure must be powered down to install outfits.")
				return
		cargo = c.structure.cargo[cindex]
		if not cargo.type in outfittype.outfits:
			c.send("This is not an outfit.")
			return
		mark = int(cargo.extra)
		report = production.update(c.structure)
		if report.outfit_space < mark:
			c.send("Insufficient outfit space.")
			return
		Outfit(cargo.type, mark).install(c.structure)
		cargo.less(1, c.structure)
		c.send("Installed a mark %d '%s' from cargo.", (mark, c.translate(cargo.type)))

def handle_load(c: Client, args: List[str]):
	
	# Validate input
	s = c.structure
	if len(args) != 3:
		c.send("Usage: load <structure ID> <cargo ID> <count>")
		return
	try:
		sid = int(args[0])
		cindex = int(args[1])
		count = int(args[2])
	except ValueError:
		c.send("Not a number.")
		return
	if count < 1:
		c.send("Count must be greater than zero.")
		return
	elif cindex >= len(s.cargo):
		c.send("Cargo does not exist.")
		return
	
	# Find docked target
	if s.dock_parent != None:
		if s.dock_parent.id != sid:
			c.send("Unable to locate docked structure.")
			return
		target = s.dock_parent
	else:
		target = None
		for ship in s.dock_children:
			if ship.id == sid:
				target = ship
				break
		if target == None:
			c.send("Unable to locate docked structure.")
			return
	
	# Move the cargo
	car = copy.copy(s.cargo[cindex])
	if car.count < count:
		c.send("Insufficient resources.")
		return
	s.cargo[cindex].less(count, s)
	car.count = count
	car.add(target)
	c.send("Loaded %d '%s' into '%d %s'", (count, car.type, sid, target.name))

def handle_set(c: Client, args: List[str]):
	if len(args) != 2:
		c.send("Usage: set <outfit ID> <setting>")
		return
	try:
		oindex = int(args[0])
		setting = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if oindex >= len(c.structure.outfits):
		c.send("Outfit does not exist.")
	elif setting < 0:
		c.send("Setting must be greater than zero.")
	else:
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.set_setting(setting)
		c.send("Updated setting of outfit '%s' to %d.", (c.translate(outfit.type.name), setting))

def handle_uninstall(c: Client, args: List[str]):
	if len(args) != 1:
		c.send("Usage: uninstall <outfit ID>")
		return
	try:
		oindex = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if oindex >= len(c.structure.outfits):
		c.send("Outfit does not exist.")
	else:
		for o in c.structure.outfits:
			if o.setting != 0:
				c.send("Structure must be powered down to uninstall outfits.")
				return
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.uninstall(c.structure)
		Cargo(outfit.type.name, 1, str(outfit.mark)).add(c.structure)
		c.send("Uninstalled outfit '%s' into cargo.", (c.translate(outfit.type.name),))


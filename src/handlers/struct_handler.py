import copy
from typing import List

import outfittype
import production
import database
import faction
import network
import strings
from client import Client
from cargo import Cargo
from outfit import Outfit

conn = database.conn

def handle_airlock(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.AIRLOCK)
		return
	elif c.structure.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED)
		return
	rc = conn.execute("UPDATE users SET structure_id = NULL WHERE structure_id = ? AND username = ?;",
		(c.structure.id, args[0],)).rowcount
	if rc > 0:
		conn.commit()
		for client in network.clients:
			if client.id != None and client.username == args[0]:
				client.structure = None
				break
		c.send(strings.STRUCT.AIRLOCK, username=args[0])
	else:
		c.send(strings.MISC.NO_OP)

def handle_board(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.BOARD)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if c.structure.dock_parent == None:
		s = None
		for struct in c.structure.dock_children:
			if struct.id == sid:
				s = struct
				break
		if s == None:
			c.send(strings.STRUCT.NO_DOCK)
			return
	else:
		if c.structure.dock_parent.id != sid:
			c.send(strings.STRUCT.NO_DOCK)
			return
		s = c.structure.dock_parent
	if not faction.has_permission(c, s, faction.BOARD_MIN):
		c.send(strings.MISC.PERMISSION_DENIED)
		return
	c.structure = s
	conn.execute("UPDATE users SET structure_id = ? WHERE id = ?;", (s.id, c.id))
	conn.commit()
	c.send(strings.STRUCT.BOARDED, id=sid, name=s.name)

def handle_eject(c: Client, args: List[str]):
	s = c.structure
	if len(args) == 0:
		if s.dock_parent == None:
			for ship in s.dock_children:
				ship.dock_parent = None
			s.dock_children = []
			conn.execute("UPDATE structures SET dock_id = NULL where dock_id = ?;", (s.id,))
			conn.commit()
			c.send(strings.STRUCT.EJECT_ALL)
		else:
			s.dock_parent.dock_children.remove(s)
			s.dock_parent = None
			conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (s.id,))
			conn.commit()
			c.send(strings.STRUCT.EJECT)
	elif len(args) == 1:
		try:
			sid = int(args[0])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		if s.dock_parent != None:
			if s.dock_parent.id == sid:
				s.dock_parent.dock_children.remove(s)
				s.dock_parent = None
				conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (s.id,))
				conn.commit()
				c.send(strings.STRUCT.EJECT)
			else:
				c.send(strings.STRUCT.NO_DOCK)
		else:
			for ship in s.dock_children:
				if ship.id == sid:
					s.dock_children.remove(ship)
					ship.dock_parent = None
					conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (ship.id,))
					c.send(strings.STRUCT.EJECTED, id=ship.id, name=ship.name)
					return
			c.send(strings.STRUCT.NO_DOCK)
	else:
		c.send(strings.USAGE.EJECT)

def handle_install(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.INSTALL)
		return
	try:
		cindex = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if cindex >= len(c.structure.cargo):
		c.send(strings.MISC.NO_CARGO)
	else:
		for o in c.structure.outfits:
			if o.setting != 0:
				c.send(strings.STRUCT.POWERED_DOWN)
				return
		cargo = c.structure.cargo[cindex]
		if not cargo.type in outfittype.outfits:
			c.send(strings.STRUCT.NOT_OUTFIT)
			return
		mark = int(cargo.extra)
		report = production.update(c.structure)
		if report.outfit_space < mark:
			c.send(strings.STRUCT.NO_OUTFIT_SPACE)
			return
		Outfit(cargo.type, mark).install(c.structure)
		cargo.less(1, c.structure)
		c.send(strings.STRUCT.INSTALLED, mark=mark, name=c.translate(cargo.type))

def handle_load(c: Client, args: List[str]):
	
	# Validate input
	s = c.structure
	if len(args) != 3:
		c.send(strings.USAGE.LOAD)
		return
	try:
		sid = int(args[0])
		cindex = int(args[1])
		count = int(args[2])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	production.update(s)
	if count < 1:
		c.send(strings.MISC.COUNT_GTZ)
		return
	elif cindex >= len(s.cargo):
		c.send(strings.MISC.NO_CARGO)
		return
	
	# Find docked target
	if s.dock_parent != None:
		if s.dock_parent.id != sid:
			c.send(strings.STRUCT.NO_DOCK)
			return
		target = s.dock_parent
	else:
		target = None
		for ship in s.dock_children:
			if ship.id == sid:
				target = ship
				break
		if target == None:
			c.send(strings.STRUCT.NO_DOCK)
			return
	
	# Move the cargo
	car = copy.copy(s.cargo[cindex])
	if car.count < count:
		c.send(strings.CRAFT.INSUFFICIENTS)
		return
	s.cargo[cindex].less(count, s)
	car.count = count
	car.add(target)
	c.send(strings.STRUCT.LOADED, count=count, type=c.translate(car.type), id=sid, name=target.name)

def handle_set(c: Client, args: List[str]):
	if len(args) != 2:
		c.send(strings.USAGE.SET)
		return
	try:
		oindex = int(args[0])
		setting = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if oindex >= len(c.structure.outfits):
		c.send(strings.STRUCT.NO_OUTFIT)
	elif setting < 0:
		c.send(strings.STRUCT.SET_GTZ)
	else:
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.set_setting(setting)
		c.send(strings.STRUCT.SET, name=c.translate(outfit.type.name), setting=setting)

def handle_supply(c: Client, args: List[str]):
	if len(args) != 2:
		c.send(strings.USAGE.SUPPLY)
		return
	s = c.structure
	try:
		sid = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	production.update(s)
	if count < 1:
		c.send(strings.STRUCT.ENERGY_GTZ)
		return
	elif count > s.energy:
		c.send(strings.STRUCT.NO_ENERGY)
		return
	
	# Find docked target
	if s.dock_parent != None:
		if s.dock_parent.id != sid:
			c.send(strings.STRUCT.NO_DOCK)
			return
		target = s.dock_parent
	else:
		target = None
		for ship in s.dock_children:
			if ship.id == sid:
				target = ship
				break
		if target == None:
			c.send(strings.STRUCT.NO_DOCK)
			return
	report = production.update(target)
	if count > report.max_energy - target.energy:
		count = int(report.max_energy - target.energy)
	
	# Transfer the energy
	s.energy-= count
	target.energy+= count
	conn.execute("UPDATE structures SET energy = ? WHERE id = ?;", (s.energy, s.id))
	conn.execute("UPDATE structures SET energy = ? WHERE id = ?;", (target.energy, sid))
	conn.commit()
	c.send(strings.STRUCT.SUPPLIED, count=count, id=sid, name=target.name)

def handle_uninstall(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.UNINSTALL)
		return
	try:
		oindex = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	if oindex >= len(c.structure.outfits):
		c.send(strings.STRUCT.NO_OUTFIT)
	else:
		for o in c.structure.outfits:
			if o.setting != 0:
				c.send(strings.STRUCT.POWERED_DOWN)
				return
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.uninstall(c.structure)
		Cargo(outfit.type.name, 1, str(outfit.mark)).add(c.structure)
		c.send(strings.STRUCT.UNINSTALLED, name=c.translate(outfit.type.name))


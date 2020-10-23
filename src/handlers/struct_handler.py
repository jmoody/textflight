import copy
from typing import List

import util
import outfittype
import production
import database
import faction
import network
import strings
import structure
from client import Client
from cargo import Cargo
from outfit import Outfit

conn = database.conn

def handle_airlock(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.AIRLOCK, error=True)
		return
	elif c.structure.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED, error=True)
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
		c.send(strings.MISC.NO_OP, error=True)

def handle_beam(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.BEAM, error=True)
		return
	try:
		sid = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	s = structure.load_structure(sid)
	if s == None or s.system.id != c.structure.system.id:
		c.send(strings.MISC.NO_STRUCT, error=True)
	elif not faction.has_permission(c, s, faction.TRANS_MIN):
		c.send(strings.MISC.PERMISSION_DENIED, error=True)
	else:
		c.structure = s
		conn.execute("UPDATE users SET structure_id = ? WHERE id = ?;", (s.id, c.id))
		conn.commit()
		c.send(strings.STRUCT.BEAMED, id=sid, name=s.name)

def handle_trans(c: Client, args: List[str]):
	if c.structure.dock_parent != None:
		s = c.structure.dock_parent
	else:
		if len(args) != 1:
			c.send(strings.USAGE.TRANS, error=True)
			return
		try:
			sid = int(args[0])
		except ValueError:
			c.send(strings.MISC.NAN, error=True)
			return
		s = None
		for struct in c.structure.dock_children:
			if struct.id == sid:
				s = struct
				break
		if s == None:
			c.send(strings.STRUCT.NO_DOCK, error=True)
			return
	if not faction.has_permission(c, s, faction.TRANS_MIN):
		c.send(strings.MISC.PERMISSION_DENIED, error=True)
		return
	c.structure = s
	conn.execute("UPDATE users SET structure_id = ? WHERE id = ?;", (s.id, c.id))
	conn.commit()
	c.send(strings.STRUCT.TRANSFERRED, id=s.id, name=s.name)
	production.update(c.structure, send_updates=True)

def handle_eject(c: Client, args: List[str]):
	s = c.structure
	if len(args) == 0:
		if s.dock_parent == None:
			for ship in s.dock_children:
				ship.dock_parent = None
			s.dock_children = []
			conn.execute("UPDATE structures SET dock_id = NULL where dock_id = ?;", (s.id,))
			production.update(c.structure, send_updates=True)
			c.send(strings.STRUCT.EJECT_ALL)
		else:
			s.dock_parent.dock_children.remove(s)
			s.dock_parent = None
			conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (s.id,))
			production.update(c.structure, send_updates=True)
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
				production.update(c.structure, send_updates=True)
				c.send(strings.STRUCT.EJECT)
			else:
				c.send(strings.STRUCT.NO_DOCK, error=True)
		else:
			for ship in s.dock_children:
				if ship.id == sid:
					s.dock_children.remove(ship)
					ship.dock_parent = None
					conn.execute("UPDATE structures SET dock_id = NULL WHERE id = ?;", (ship.id,))
					production.update(c.structure, send_updates=True)
					c.send(strings.STRUCT.EJECTED, id=ship.id, name=ship.name)
					return
			c.send(strings.STRUCT.NO_DOCK, error=True)
	else:
		c.send(strings.USAGE.EJECT, error=True)

def handle_install(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.INSTALL, error=True)
		return
	cargo = util.search_cargo(" ".join(args), s.cargo, c)
	if cargo == None:
		c.send(strings.MISC.NO_CARGO, error=True)
		return
	if not cargo.type in outfittype.outfits:
		c.send(strings.STRUCT.NOT_OUTFIT, error=True)
		return
	mark = int(cargo.extra)
	report = production.update(c.structure)
	if report.outfit_space < mark:
		c.send(strings.STRUCT.NO_OUTFIT_SPACE, error=True)
		return
	Outfit(cargo.type, mark, cargo.theme).install(c.structure)
	cargo.less(1, c.structure)
	c.send(strings.STRUCT.INSTALLED, mark=mark, name=c.translate(cargo.type))

def handle_load(c: Client, args: List[str]):
	
	# Validate input
	s = c.structure
	if len(args) < 3:
		c.send(strings.USAGE.LOAD, error=True)
		return
	try:
		count = int(args.pop(0))
		sid = int(args.pop(0))
	except ValueError:
		c.send(strings.MISC.NAN)
		return
	car = util.search_cargo(" ".join(args), s.cargo, c)
	if car == None:
		c.send(strings.MISC.NO_CARGO, error=True)
		return
	production.update(s)
	if count < 0:
		c.send(strings.MISC.COUNT_GTZ, error=True)
		return
	
	# Find docked target
	if s.dock_parent != None:
		target = s.dock_parent
		if target.id != sid:
			c.send(strings.STRUCT.NO_DOCK, error=True)
			return
	else:
		target = None
		for ship in s.dock_children:
			if ship.id == sid:
				target = ship
				break
		if target == None:
			c.send(strings.STRUCT.NO_DOCK, error=True)
			return
	
	# Move the cargo
	car2 = copy.copy(car)
	if count == 0:
		count = car2.count
	elif car2.count < count:
		count = car2.count
	car.less(count, s)
	car2.count = count
	car2.add(target)
	c.send(strings.STRUCT.LOADED, count=count, type=c.translate(car.type), id=target.id, name=target.name)
	production.update(c.structure, send_updates=True)

def handle_set(c: Client, args: List[str]):
	if len(args) != 2:
		c.send(strings.USAGE.SET, error=True)
		return
	try:
		setting = int(args.pop(0))
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	outfit = util.search_outfits(" ".join(args), c.structure.outfits, c)
	if outfit == None:
		c.send(strings.STRUCT.NO_OUTFIT, error=True)
	elif setting < 0:
		c.send(strings.STRUCT.SET_GTZ, error=True)
	elif setting > 1024:
		c.send(strings.STRUCT.SET_LT, error=True)
	else:
		production.update(c.structure)
		outfit.set_setting(setting)
		c.send(strings.STRUCT.SET, name=c.translate(outfit.type.name), setting=setting)
		production.update(c.structure, send_updates=True)

def handle_supply(c: Client, args: List[str]):
	if len(args) < 1:
		c.send(strings.USAGE.SUPPLY, error=True)
		return
	s = c.structure
	try:
		count = int(args[0])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	production.update(s)
	if count < 1:
		c.send(strings.STRUCT.ENERGY_GTZ, error=True)
		return
	elif count > s.energy:
		c.send(strings.STRUCT.NO_ENERGY, error=True)
		return
	
	# Find docked target
	if s.dock_parent != None:
		target = s.dock_parent
	else:
		if len(args) != 2:
			c.send(strings.USAGE.SUPPLY, error=True)
			return
		try:
			sid = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN, error=True)
			return
		target = None
		for ship in s.dock_children:
			if ship.id == sid:
				target = ship
				break
		if target == None:
			c.send(strings.STRUCT.NO_DOCK, error=True)
			return
	report = production.update(target)
	if count > report.max_energy - target.energy:
		count = int(report.max_energy - target.energy)
	
	# Transfer the energy
	s.energy-= count
	target.energy+= count
	conn.execute("UPDATE structures SET energy = ? WHERE id = ?;", (s.energy, s.id))
	conn.execute("UPDATE structures SET energy = ? WHERE id = ?;", (target.energy, target.id))
	conn.commit()
	c.send(strings.STRUCT.SUPPLIED, count=count, id=target.id, name=target.name)
	production.update(c.structure, send_updates=True)

def handle_swap(c: Client, args: List[str]):
	if len(args) != 2:
		c.send(strings.USAGE.SWAP)
		return
	try:
		oindex1 = int(args[0])
		oindex2 = int(args[1])
	except ValueError:
		c.send(strings.MISC.NAN, error=True)
		return
	if oindex1 >= len(c.structure.outfits) or oindex2 >= len(c.structure.outfits):
		c.send(strings.STRUCT.NO_OUTFIT, error=True)
		return
	outfit1 = c.structure.outfits[oindex1]
	outfit2 = c.structure.outfits[oindex2]
	conn.execute("UPDATE outfits SET type = ?, mark = ?, setting = ?, counter = ? WHERE id = ?;",
		(outfit1.type.name, outfit1.mark, outfit1.setting, outfit1.counter, outfit2.id))
	conn.execute("UPDATE outfits SET type = ?, mark = ?, setting = ?, counter = ? WHERE id = ?;",
		(outfit2.type.name, outfit2.mark, outfit2.setting, outfit2.counter, outfit1.id))
	conn.commit()
	c.structure.outfits[oindex1] = outfit2
	c.structure.outfits[oindex2] = outfit1
	id1 = outfit1.id
	outfit1.id = outfit2.id
	outfit2.id = outfit1.id
	c.send(strings.STRUCT.SWAPPED)

def handle_uninstall(c: Client, args: List[str]):
	if len(args) != 1:
		c.send(strings.USAGE.UNINSTALL, error=True)
		return
	outfit = util.search_outfits(" ".join(args), c.structure.outfits, c)
	if outfit == None:
		c.send(strings.STRUCT.NO_OUTFIT, error=True)
		return
	production.update(c.structure)
	outfit.uninstall(c.structure)
	Cargo(outfit.type.name, 1, str(outfit.mark), outfit.theme).add(c.structure)
	c.send(strings.STRUCT.UNINSTALLED, name=c.translate(outfit.type.name))


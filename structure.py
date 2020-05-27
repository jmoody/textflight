import weakref

import database
import cargo
import outfit
import queue
from system import System

conn = database.conn

registry = weakref.WeakValueDictionary()

class Structure:
	
	_destroyed = False
	
	def __init__(self, stup) -> None:
		
		# Load general info
		self.id = stup["id"]
		self.name = stup["name"]
		self.owner_id = stup["owner_id"]
		self.type = stup["type"]
		self.outfit_space = stup["outfit_space"]
		
		# Load status info
		self.heat = stup["heat"]
		self.energy = stup["energy"]
		self.shield = stup["shield"]
		self.interrupt = stup["interrupt"]
		self.warp_charge = stup["warp_charge"]
		self.mining_progress = stup["mining_progress"]
		
		# Load position info
		self.system = System(stup["sys_id"])
		self.planet_id = stup["planet_id"]
		self._dock_id = stup["dock_id"]
		self.dock_parent = None
		self.dock_children = []
		
		# Load outfits
		self.outfits = []
		for out in conn.execute("SELECT * FROM outfits WHERE structure_id = ?;", (self.id,)):
			self.outfits.append(outfit.load_outfit(out))
		
		# Load cargo
		self.cargo = []
		for car in conn.execute("SELECT * FROM cargo WHERE structure_id = ?;", (self.id,)):
			self.cargo.append(cargo.load_cargo(car))
		
		# Load crafting queue
		self.craft_queue = []
		for q in conn.execute("SELECT * FROM craft_queue WHERE structure_id = ?;", (self.id,)):
			self.craft_queue.append(queue.load_craft_queue(q))
		
		# Combat
		self.targets = weakref.WeakSet()
		self.tree = weakref.WeakSet()
		self.tree.add(self)
	
	def land(self, planet_id: int) -> None:
		conn.execute("UPDATE structures SET planet_id = ? WHERE id = ?;", (planet_id, self.id))
		self.planet_id = planet_id
		conn.commit()
	
	def dock(self, target_id: int):
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (target_id, self.id))
		self.dock_id = target_id
		conn.commit()
	
	def rename(self, name: str) -> None:
		conn.execute("UPDATE structures SET name = ? WHERE id = ?;", (name, self.id))
		self.name = name
		conn.commit()

def load_structure(sid: int) -> Structure:
	if sid in registry:
		return registry[sid]
	stup = conn.execute("SELECT * FROM structures WHERE id = ?;", (sid,)).fetchone()
	if stup == None:
		return None
	s = Structure(stup)
	registry[sid] = s
	if s._dock_id != None:
		s.dock_parent = load_structure(s._dock_id)
		if not s in s.dock_parent.dock_children:
			s.dock_parent.dock_children.append(s)
	else:
		for did in conn.execute("SELECT id FROM structures WHERE dock_id = ?;", (sid,)):
			s.dock_children.append(load_structure(did["id"]))
	return s

def create_structure(name, owner, stype, outfit_space, sys_id, planet_id = None, dock_id = None) -> Structure:
	c = conn.execute("INSERT INTO structures (name, owner_id, type, outfit_space, sys_id, planet_id, dock_id) VALUES (?, ?, ?, ?, ?, ?, ?);",
		(name, owner, stype, outfit_space, sys_id, planet_id, dock_id))
	conn.commit()
	return load_structure(c.lastrowid)


import database
import cargo
import outfit
from system import System

conn = database.conn

class Structure:
	
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
		self.mining_interrupt = stup["mining_interrupt"]
		self.warp_charge = stup["warp_charge"]
		
		# Load position info
		self.system = System(stup["sys_id"])
		self.planet_id = stup["planet_id"]
		self.dock_id = stup["dock_id"]
		
		# Load outfits
		self.outfits = []
		for out in conn.execute("SELECT * FROM outfits WHERE structure_id = ?", (self.id,)):
			self.outfits.append(outfit.load_outfit(out))
		
		# Load cargo
		self.cargo = []
		for car in conn.execute("SELECT * FROM cargo WHERE structure_id = ?", (self.id,)):
			self.cargo.append(cargo.load_cargo(car))
	
	def land(self, planet_id: int) -> None:
		conn.execute("UPDATE structures SET planet_id = ? WHERE id = ?;", (planet_id, self.id))
		self.planet_id = planet_id
		conn.commit()
	
	def dock(self, target_id: int):
		conn.execute("UPDATE structures SET dock_id = ? WHERE id = ?;", (target_id, self.id))
		self.dock_id = target_id
		conn.commit()
	
	def launch(self) -> None:
		conn.execute("UPDATE structures SET planet_id = NULL, dock_id = NULL WHERE id = ?;", (self.id,))
		self.planet_id = None
		self.dock_id = None
		conn.commit()
	
	def jump(self, sys_id: int) -> None:
		conn.execute("UPDATE structures SET warp_charge = 0, system_id = ? WHERE id=?;", (sys_id, self.id))
		self.system = System(sys_id)
		conn.commit()
	
	def rename(self, name: str) -> None:
		conn.execute("UPDATE structures SET name = ? WHERE id = ?;", (name, self.id))
		self.name = name
		conn.commit()

def create_structure(name, owner, stype, outfit_space, sys_id, planet_id = None, dock_id = None) -> Structure:
	c = conn.cursor()
	c.execute("INSERT INTO structures (name, owner_id, type, outfit_space, sys_id, planet_id, dock_id) VALUES (?, ?, ?, ?, ?, ?, ?);",
		(name, owner, stype, outfit_space, sys_id, planet_id, dock_id))
	c.execute("SELECT * FROM structures WHERE id = ?;", (c.lastrowid,))
	conn.commit()
	return Structure(c.fetchone())


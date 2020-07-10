import hashlib
import enum
import random
from typing import List, Tuple

import config
import strings

syst = config.get_section("terrain")
SEED = syst.getint("Seed")
BRIGHTNESS_BITS = syst.getint("BrightnessBits")
ASTEROID_RICHNESS_BITS = syst.getint("AsteroidRichnessBits")
PLANET_COUNT_BITS = syst.getint("PlanetCountBits")
LINK_BITS = syst.getint("LinkBits")
DRAG_BITS = syst.getint("DragBits")

class PlanetType(enum.Enum):
	GAS = 0
	BARREN = 1
	FROZEN = 2
	GREENHOUSE = 3
	HABITABLE = 4

class AsteroidType(enum.Enum):
	IRON = "Iron Ore"
	CARBON = "Carbon Ore"
	COPPER = "Copper Ore"
	SILICON = "Silicon Ore"
	URANIUM = "Uranium Ore"

class System:
	
	def __init__(self, sys_id: int) -> None:
		self.id = sys_id
		self.id_db = sys_id
		if self.id_db > pow(2, 63):
			self.id_db-= 1 << 64
		self.x, self.y = to_system_coords(self.id)
		r = get_random(self.id)
		self.brightness = r.getrandbits(BRIGHTNESS_BITS)
		self.asteroid_type = r.choice(list(AsteroidType))
		self.asteroid_richness = r.getrandbits(ASTEROID_RICHNESS_BITS)
		self.planets = []
		for i in range(r.getrandbits(PLANET_COUNT_BITS)):
			self.planets.append(Planet(r))
	
	def get_links(self) -> List[int]:
		links = []
		for yo in range(-1, 2):
			for xo in range(-1, 2):
				if xo == 0 and yo == 0:
					continue
				lx = self.x + xo
				ly = self.y + yo
				if lx < 0:
					lx+= 1 << 32
				elif lx + 1 > pow(2, 32):
					lx-= 1 << 32
				if ly < 0:
					ly+= 1 << 32
				elif ly + 1 > pow(2, 32):
					ly-= 1 << 32
				lid = to_system_id(lx, ly)
				drag = get_link_drag(self.id, lid)
				if drag != 0:
					links.append((lid, drag, xo, yo))
		return links

class Planet:
	ptype = None
	
	def __init__(self, r: random.Random) -> None:
		type_roll = r.randint(0, 1000)
		if type_roll <= 400:
			self.ptype = PlanetType.GAS
		elif type_roll <= 800:
			self.ptype = PlanetType.BARREN
		elif type_roll <= 900:
			self.ptype = PlanetType.FROZEN
		elif type_roll <= 999:
			self.ptype = PlanetType.GREENHOUSE
		else:
			self.ptype = PlanetType.HABITABLE

def get_link_drag(sys1_id: int, sys2_id: int) -> int:
	if sys1_id < sys2_id:
		link_id = sys1_id << 64 | sys2_id
	else:
		link_id = sys2_id << 64 | sys1_id
	r = get_random(link_id)
	if r.getrandbits(LINK_BITS):
		return 0
	drag = r.getrandbits(DRAG_BITS)
	return drag

def to_system_coords(sys_id: int) -> Tuple[int, int]:
	x = sys_id >> 32
	y = sys_id & 0x00000000FFFFFFFF
	return (x, y)

def to_system_id(x: int, y: int) -> int:
	return x << 32 | y

def get_random(seed: int) -> random.Random:
	r = random.Random()
	digest = hashlib.sha256()
	seeddat = (seed + SEED).to_bytes(16, byteorder='big')
	digest.update(seeddat)
	r.seed(digest.digest())
	return r


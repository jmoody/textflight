from typing import List, Tuple
import enum
import random

import config

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
	IRON = "Iron ore"
	CARBON = "Carbon Ore"
	COPPER = "Copper Ore"
	SILICON = "Silicon Ore"
	URANIUM = "Uranium Ore"

class System:
	
	def __init__(self, sys_id: int) -> None:
		self.id = sys_id
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
		for xo in range(-1, 2):
			for yo in range(-1, 2):
				if xo == 0 and yo == 0:
					continue
				drag = get_link_drag(self.id, to_system_id(self.x + xo, self.y + yo))
				if drag != 0:
					links.append((xo, yo, drag))
		return links

class Planet:
	name = None
	ptype = None
	
	def __init__(self, r: random.Random) -> None:
		type_roll = r.randint(0, 1000) / 10
		if type_roll <= 40:
			self.ptype = PlanetType.GAS
		elif type_roll <= 80:
			self.ptype = PlanetType.BARREN
		elif type_roll <= 90:
			self.ptype = PlanetType.FROZEN
		elif type_roll <= 99.9:
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
	r.seed(seed + SEED)
	return r


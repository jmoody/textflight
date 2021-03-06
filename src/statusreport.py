
class StatusReport:
	
	now = None
	_stime = 0
	shutdown = False
	
	mass = 0
	outfit_space = 0
	heat_rate = 0
	max_heat = 0
	energy_rate = 0
	max_energy = 0
	overheat_time = None
	powerloss_time = None
	
	_fission_cells = 0
	_fusion_cells = 0
	_supplies = 0
	
	shield_rate = 0
	max_shield = 0
	has_shields = False
	
	warp_rate = 0
	normal_warp = 0
	antigravity = 0
	
	electron_damage = 0
	emp_damage = 0
	hull_damage = 0
	plasma_damage = 0
	has_weapons = False
	
	mining_power = 0
	mining_interval = 0
	assembly_rate = 0
	shipyard = 0
	
	crew = 0
	food = 0
	attack = 1
	defence = 1
	
	def __init__(self):
		self.generators = {}
		self.living_spaces = []
		self._gtimes = {}
	
	def zero(self) -> None:
		self.heat_rate = 0
		self.energy_rate = 0
		self.shield_rate = 0
		self.warp_rate = 0
		self.antigravity = 0
		self.electron_damage = 0
		self.emp_damage = 0
		self.hull_damage = 0
		self.plasma_damage = 0
		self.has_weapons = False
		self.mining_power = 0
		self.mining_interval = 0
		self.assembly_rate = 0
		self.shipyard = 0
		self.crew = 0
		self.food = 0
		self.attack = 1
		self.defence = 1
	
	def to_str(self, s) -> str:
		out = "STATUSREPORT BEGIN\n"
		
		# StatusReport values
		out+= "now: %f\n" % self.now
		out+= "stime: %f\n" % self._stime
		out+= "shutdown: %d\n" % int(self.shutdown)
		out+= "mass: %f\n" % self.mass
		out+= "outfit_space: %f\n" % self.outfit_space
		out+= "heat_rate: %f\n" % self.heat_rate
		out+= "max_heat: %f\n" % self.max_heat
		out+= "energy_rate: %f\n" % self.energy_rate
		out+= "max_energy: %f\n" % self.max_energy
		out+= "shield_rate: %f\n" % self.shield_rate
		out+= "max_shield: %f\n" % self.max_shield
		out+= "warp_rate: %f\n" % self.warp_rate
		out+= "normal_warp: %f\n" % self.normal_warp
		out+= "antigravity: %f\n" % self.antigravity
		out+= "electron_damage: %f\n" % self.electron_damage
		out+= "emp_damage: %f\n" % self.emp_damage
		out+= "hull_damage: %f\n" % self.hull_damage
		out+= "plasma_damage: %f\n" % self.plasma_damage
		out+= "mining_power: %f\n" % self.mining_power
		out+= "assembly_rate: %f\n" % self.assembly_rate
		out+= "shipyard: %f\n" % self.shipyard
		out+= "crew: %f\n" % self.crew
		out+= "food: %f\n" % self.food
		out+= "attack: %f\n" % self.attack
		out+= "defence: %f\n" % self.defence
		
		# Structure values
		out+= "id: %d\n" % s.id
		out+= "created_at: %f\n" % s.created_at
		out+= "name: %s\n" % s.name
		out+= "type: %s\n" % s.type
		out+= "total_outfit_space: %d\n" % s.outfit_space
		out+= "heat: %f\n" % s.heat
		out+= "energy: %f\n" % s.energy
		out+= "shield: %f\n" % s.shield
		out+= "warp_charge: %f\n" % s.warp_charge
		out+= "mining_progress: %f\n" % s.mining_progress
		out+= "sys_id: %d\n" % s.system.id
		if s.planet_id != None:
			out+= "planet_id: %d\n" % s.planet_id
		out+= "asteroid_type: %s\n" % s.system.asteroid_type.value
		out+= "asteroid_richness: %d\n" % s.system.asteroid_richness
		for planet in s.system.planets:
			out+= "planet: %d\n" % planet.ptype.value
		if s.dock_parent != None:
			out+= "dock_id: %d\n" % s.dock_parent.id
		out+= "queue_size: %d\n" % len(s.craft_queue)
		out+= "targets_size: %d\n" % len(s.targets)
		
		out+= "STATUSREPORT END\n"
		return out


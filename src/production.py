import time
from typing import Tuple

import database
import crafting
import config
import system
from structure import Structure
from cargo import Cargo



#
# Oh boy, if you have to edit this file, I do *not* envy you...
# I'm sorry in advance.
#
# Ok, here's a simple explanation of how this works. Since ships in combat have
# stats that affect each other, we need to update them at the same time, and
# things are further complicated by generators which change the rate at which
# energy is consumed/heat is produced. The way we handle this is by updating
# structures in steps; we determine the "stime" for each structure, which is the
# next time the rate of change in that structure's stats will change. Then we
# take the lowest stime for all of the structures involved (capping out at the
# current time, since we don't want to update structures into the future), and
# update all the structures to that time. If a structure shuts down, we remove
# it from the cycle, as there's no longer any point in updating it.
#


conn = database.conn

MAX_ASTEROID_RICHNESS = pow(2, system.ASTEROID_RICHNESS_BITS) - 1
minc = config.get_section("mining")
MINING_INTERVAL_BASE = minc.getint("MiningInterval")
GAS_INTERVAL_MULTIPLIER = minc.getint("GasIntervalMultiplier")
HYDROGEN_COUNT = minc.getint("HydrogenCount")
OXYGEN_COUNT = minc.getint("OxygenCount")
XENON_COUNT = minc.getint("XenonCount")
PLANET_HEAT_RATE = minc.getfloat("PlanetHeat")
BREED_RATE = config.get_section("crafting").getint("BreedRate")

class StatusReport:
	
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

def update(s: Structure, now=None) -> StatusReport:
	structs = list(s.tree)
	if now == None:
		now = time.time()
	report = None
	
	# Update all linked structures
	while len(structs) > 0:
		min_stime = now
		reports = {}
		
		# Determine the next stime
		for struct in structs.copy():
			r = determine_stime(struct, now)
			reports[struct] = r
			if r._stime != s.interrupt:
				reports[struct] = r
				min_stime = min(min_stime, r._stime)
		
		# Update all structures to the lowest stime
		for struct in structs.copy():
			r = reports[struct]
			
			# Remove structure from tree if it's shut down
			do_write = False
			if r.shutdown or min_stime == now:
				if struct == s:
					report = r
				structs.remove(struct)
				do_write = True
			else:
				r._stime = min_stime
				r.now = min_stime
			
			# Update structure to stime
			update_step(struct, r, do_write)
	
	# Return StatusReport for target structure
	return report

def determine_stime(s: Structure, now: float) -> StatusReport:
	report = StatusReport()
	report.outfit_space = s.outfit_space
	report.now = now
	
	# Apply planetary effects
	if s.planet_id != None:
		ptype = s.system.planets[s.planet_id].ptype
		if ptype == system.PlanetType.BARREN or ptype == system.PlanetType.GREENHOUSE:
			report.heat_rate+= PLANET_HEAT_RATE * s.outfit_space
	
	# Add mass for cargo and crafting queue
	report.mass+= s.outfit_space
	for cargo in s.cargo:
		try:
			report.mass+= int(cargo.extra) * cargo.count
		except:
			report.mass+= cargo.count
		if cargo.type == "Uranium Fuel Cell":
			report._fission_cells+= cargo.count
		elif cargo.type == "Hydrogen Fuel Cell":
			report._fusion_cells+= cargo.count
		elif cargo.type == "Supply Packages":
			report._supplies+= cargo.count
	for q in s.craft_queue:
		try:
			report.mass+= int(q.extra) * (q.count + 1)
		except:
			report.mass+= q.count + 1
	
	# Load outfit properties
	for outfit in s.outfits:
		report.mass+= outfit.mark
		report.outfit_space-= outfit.mark
		
		report.antigravity+= outfit.prop("antigravity", True)
		report.assembly_rate+= outfit.prop("assembler", True)
		report.electron_damage+= outfit.prop("electron", True)
		report.emp_damage+= outfit.prop("emp", True)
		report.energy_rate+= outfit.prop("energy")
		report.heat_rate+= outfit.heat_rate()
		report.hull_damage+= outfit.prop("hull", True)
		report.max_energy+= round(outfit.prop_nocharge("max_energy", True))
		report.max_heat+= round(outfit.prop_nocharge("max_heat", True))
		report.max_shield+= round(outfit.prop_nocharge("max_shield"))
		report.mining_power+= outfit.prop("mining", True)
		report.plasma_damage+= outfit.prop("plasma", True)
		report.shield_rate+= outfit.prop("shield", True)
		report.shipyard+= outfit.prop("shipyard", True)
		report.energy_rate-= outfit.prop("solar", True) * (s.system.brightness / (pow(2, system.BRIGHTNESS_BITS) - 1))
		report.warp_rate+= outfit.prop("warp", True)
		report.normal_warp+= outfit.prop_nocharge("warp", True)
		report.food+= outfit.prop("food", True)
		if s.type == "base":
			report.energy_rate+= outfit.prop("geo")
			report.heat_rate+= outfit.prop("sink")
		if outfit.prop_nocharge("shield") > 0:
			report.has_shields = True
		if outfit.prop_nocharge("fission") > 0:
			if outfit.setting > 0:
				fuel = outfit.counter + report._fission_cells * outfit.prop_nocharge("fission", True)
				report.generators[outfit] = s.interrupt + fuel / outfit.performance()
		elif outfit.prop_nocharge("fusion") > 0:
			if outfit.setting > 0:
				fuel = outfit.counter + report._fusion_cells * outfit.prop_nocharge("fusion", True)
				report.generators[outfit] = s.interrupt + fuel / outfit.performance()
		elif outfit.prop_nocharge("supplies") > 0:
			if outfit.setting > 0:
				fuel = outfit.counter + report._supplies * outfit.prop_nocharge("supplies", True)
				report.generators[outfit] = s.interrupt + fuel / outfit.performance()
		elif outfit.prop_nocharge("crew") > 0:
			report.living_spaces.append(outfit)
	
	# Apply properties from enemy weapons
	for struct in s.targets:
		for outfit in struct.outfits:
			report.heat_rate+= outfit.prop("plasma", True)
			report.energy_rate+= outfit.prop("emp", True)
			report.shield_rate-= outfit.prop("electron", True)
	
	# Determine whether we have weapons or not
	if report.electron_damage > 0 or report.emp_damage > 0 or report.plasma_damage > 0 or report.hull_damage > 0:
		report.has_weapons = True
	
	# Determine stime for heat
	stime = report.now
	if report.heat_rate >= 0:
		if s.heat == report.max_heat:
			report.overheat_time = 0
		elif report.heat_rate > 0:
			report.overheat_time = s.interrupt + (report.max_heat - s.heat) / report.heat_rate
		if report.overheat_time != None and report.overheat_time < stime:
			stime = report.overheat_time
			report.shutdown = True
	
	# Determine stime for generators
	if len(report.generators) > 0:
		gtime = sorted(report.generators.values())[0]
		if gtime < stime:
			stime = gtime
	
	# Determine stime for energy
	if report.energy_rate >= 0:
		if s.energy == 0:
			report.powerloss_time = 0
		elif report.energy_rate > 0:
			report.powerloss_time = s.interrupt + s.energy / report.energy_rate
		if report.powerloss_time != None and report.powerloss_time < stime:
			stime = report.powerloss_time
			report.shutdown = True
	
	report._stime = stime
	return report

def update_step(s: Structure, report: StatusReport, do_write: bool):
	stime = report._stime
	
	# Update counters and fuel
	for outfit, fuelout in report.generators.items():
		
		# Determine seconds of fuel used
		used = stime - s.interrupt
		used*= outfit.performance()
		left = 0
		
		# Subtract directly from counter if we can
		if used < outfit.counter:
			left = outfit.counter - used
		
		# Subtract from cargo
		elif outfit.prop("fission") > 0:
			
			# Determine how many fuel items have been consumed
			# Add one to refill the outfit charge
			fission = outfit.prop_nocharge("fission", True)
			fuel_used = int(used / fission) + 1
			
			# Figure out what the outfit charge should be now
			if used == fuelout - s.interrupt:
				left = 0
			else:
				left = fission - used % fission
			
			# Remove from cargo
			Cargo("Uranium Fuel Cell", fuel_used).remove(s)
			Cargo("Empty Cell", fuel_used).add(s)
		
		elif outfit.prop("fusion") > 0:
			
			# The same as the above code, but for fusion
			fusion = outfit.prop_nocharge("fusion", True)
			fuel_used = int(used / fusion) + 1
			if used == fuelout - s.interrupt:
				left = 0
			else:
				left = fusion - used % fusion
			Cargo("Hydrogen Fuel Cell", fuel_used).remove(s)
			Cargo("Empty Cell", fuel_used).add(s)
		
		elif outfit.prop("supplies") > 0:
			
			# The same as the above code, but for supplies
			supplies = outfit.prop_nocharge("supplies", True)
			fuel_used = int(used / supplies) + 1
			if used == fuelout - s.interrupt:
				left = 0
			else:
				left = supplies - used % supplies
			Cargo("Supply Packages", fuel_used).remove(s)
		
		# Update outfit counter
		outfit.set_counter(left)
		if left == 0:
			outfit.set_setting(0)
	
	# Update if systems have not failed and have been active for more than 0 seconds
	if s.interrupt != stime and not report.shutdown:
		active = stime - s.interrupt
		report.mining_interval = update_mining(s, report.mining_power, active)
		if report.assembly_rate > 0:
			update_assembly(s, report.assembly_rate, active)
		s.heat+= active * report.heat_rate
		s.energy-= active * report.energy_rate
		s.shield+= active * report.shield_rate
		s.warp_charge+= active * report.warp_rate
		
		# Update crew
		for outfit in report.living_spaces:
			max_crew = max(min(outfit.prop("crew", True), report.food), 0)
			if s.type == "base" and s.planet_id != None and s.system.planets[s.planet_id].ptype == system.PlanetType.HABITABLE:
				max_crew = outfit.prop("crew", True) * 128
			else:
				report.food-= outfit.counter
			if max_crew < outfit.counter:
				outfit.set_counter(max(max_crew, outfit.counter - active / BREED_RATE))
			else:
				outfit.set_counter(min(max_crew, outfit.counter + active / BREED_RATE))
			report.crew+= outfit.counter
	
	# Handle system failure
	if report.shutdown:
		for outfit in s.outfits:
			outfit.set_setting(0)
			if outfit.type == "Living Spaces":
				outfit.set_counter(0)
		report.zero()
	
	# Write to database
	s.heat = max(s.heat, 0)
	s.energy = max(min(report.max_energy, s.energy), 0)
	s.shield = max(min(report.max_shield, s.shield), 0)
	if report.normal_warp > 0:
		s.warp_charge = max(min(min(report.warp_rate / report.normal_warp * report.mass, report.mass), s.warp_charge), 0)
	s.interrupt = report.now
	if do_write:
		conn.execute("UPDATE structures SET interrupt = ?, heat = ?, energy = ?, shield = ?, warp_charge = ?, mining_progress = ? WHERE id = ?;",
			(s.interrupt, s.heat, s.energy, s.shield, s.warp_charge, s.mining_progress, s.id))
		conn.commit()
	
	return report

def update_mining(s: Structure, beam_power: float, active: float) -> float:
	if beam_power == 0:
		return 0
	elapsed = s.mining_progress + active
	interval = MINING_INTERVAL_BASE / beam_power
	if s.planet_id != None:
		ptype = s.system.planets[s.planet_id].ptype
	if s.planet_id == None:
		if s.system.asteroid_richness == 0:
			return 0
		interval*= MAX_ASTEROID_RICHNESS / s.system.asteroid_richness
		count = int(elapsed / interval)
		if count > 0:
			Cargo(s.system.asteroid_type.value, count).add(s)
	elif ptype == system.PlanetType.GAS or ptype == system.PlanetType.GREENHOUSE:
		interval*= GAS_INTERVAL_MULTIPLIER
		count = int(elapsed / interval)
		if count > 0:
			Cargo("Hydrogen", count * HYDROGEN_COUNT).add(s)
			Cargo("Oxygen", count * OXYGEN_COUNT).add(s)
			Cargo("Xenon", count * XENON_COUNT).add(s)
	else:
		s.mining_progress = 0
		return interval
	s.mining_progress = elapsed - interval * count
	return interval

def update_assembly(s: Structure, assembly_rate: float, active: float) -> None:
	for q in s.craft_queue:
		craft_time = crafting.craft_time(q)
		work_done = active * assembly_rate - q.work
		if work_done > 0:
			finished = int(work_done / craft_time)
			work_done-= finished * craft_time
			if q.count > 0:
				q.work = craft_time - work_done
			else:
				q.work = -1
			finished = min(q.count, finished)
			finished+= 1
		else:
			q.work = -work_done
			finished = 0
		if finished > 0:
			Cargo(q.type, finished, q.extra).add(s)
		q.less(finished, s)


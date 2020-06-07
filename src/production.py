import time
from typing import Tuple

import database
import crafting
import config
import system
from structure import Structure
from cargo import Cargo

conn = database.conn

MAX_ASTEROID_RICHNESS = pow(2, system.ASTEROID_RICHNESS_BITS)
minc = config.get_section("mining")
MINING_INTERVAL_BASE = minc.getint("MiningInterval")
GAS_INTERVAL_MULTIPLIER = minc.getint("GasIntervalMultiplier")
HYDROGEN_COUNT = minc.getint("HydrogenCount")
OXYGEN_COUNT = minc.getint("OxygenCount")
XENON_COUNT = minc.getint("XenonCount")
PLANET_HEAT_RATE = minc.getfloat("PlanetHeat")

class StatusReport:
	
	_stime = 0
	
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
	
	def __init__(self):
		self.generators = {}
		self._gtimes = {}

def update(s: Structure, now=None) -> StatusReport:
	structs = list(s.tree)
	if now == None:
		now = time.time()
	report = None
	while len(structs) > 0:
		min_stime = now
		reports = {}
		for struct in structs.copy():
			r = determine_stime(struct, now)
			reports[struct] = r
			if r._stime != s.interrupt:
				reports[struct] = r
				min_stime = min(min_stime, r._stime)
		for struct in structs.copy():
			r = reports[struct]
			if r._stime <= min_stime:
				if struct == s:
					report = r
				structs.remove(struct)
			else:
				r._stime = min_stime
				r.now = min_stime
			update_step(struct, r)
	return report

def determine_stime(s: Structure, now: float) -> StatusReport:
	report = StatusReport()
	report.outfit_space = s.outfit_space
	report.now = now
	
	# Apply planetary effects
	if s.planet_id != None:
		ptype = s.system.planets[s.planet_id]
		if ptype == system.PlanetType.BARREN or ptype == system.PlanetType.GREENHOUSE:
			report.heat_rate+= PLANET_HEAT_RATE * s.outfit_space
	
	# Parse outfits and cargo
	report.mass+= len(s.craft_queue)
	for cargo in s.cargo:
		try:
			report.mass+= int(cargo.extra) * cargo.count
		except:
			report.mass+= cargo.count
		if cargo.type == "Uranium Fuel Cell":
			report._fission_cells+= cargo.count
		elif cargo.type == "Hydrogen Fuel Cell":
			report._fusion_cells+= cargo.count
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
		report.energy_rate-= outfit.prop("solar", True) * (s.system.brightness / pow(2, system.BRIGHTNESS_BITS))
		report.warp_rate+= outfit.prop("warp", True)
		report.normal_warp+= outfit.prop_nocharge("warp", True)
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
	for struct in s.targets:
		for outfit in struct.outfits:
			report.heat_rate+= outfit.prop("plasma", True)
			report.energy_rate+= outfit.prop("emp", True)
			report.shield_rate-= outfit.prop("electron", True)
	if report.electron_damage > 0 or report.emp_damage > 0 or report.plasma_damage > 0 or report.hull_damage > 0:
		report.has_weapons = True
	
	# Determine stime for heat
	stime = report.now
	if report.heat_rate >= 0:
		if s.heat == report.max_heat:
			report.overheat_time = s.interrupt
		elif report.heat_rate > 0:
			report.overheat_time = s.interrupt + (report.max_heat - s.heat) / report.heat_rate
		if report.overheat_time != None and report.overheat_time < stime:
			stime = report.overheat_time
	
	# Determine stime for generators
	gtime = s.interrupt
	ctime = None
	for outfit, fuelout in sorted(report.generators.items(), key=lambda item: item[1]):
		if fuelout >= stime:
			continue
		if report.energy_rate > 0:
			ctime = s.interrupt + s.energy / report.energy_rate
			if ctime < fuelout and ctime < stime:
				stime = ctime
		if ctime == None or ctime >= fuelout:
			s.energy-= (fuelout - gtime) * report.energy_rate
			s.energy = max(min(report.max_energy, s.energy), 0)
			gtime = fuelout
			report._gtimes[fuelout] = s.energy
			report.energy_rate-= outfit.prop("energy")
	
	# Determine stime for energy
	if report.energy_rate >= 0:
		if s.energy == 0:
			report.powerloss_time = s.interrupt
		elif report.energy_rate > 0:
			report.powerloss_time = s.interrupt + s.energy / report.energy_rate
		if report.powerloss_time != None and report.powerloss_time < stime:
			stime = report.powerloss_time
	
	report._stime = stime
	return report

def update_step(s: Structure, report: StatusReport):
	stime = report._stime
	if len(report._gtimes) > 0:
		gtime = sorted(report._gtimes)[-1]
		s.energy = report._gtimes[gtime]
	else:
		gtime = s.interrupt
	
	# Update counters and fuel
	for outfit, fuelout in report.generators.items():
		used = min(fuelout, stime) - s.interrupt
		used*= outfit.performance()
		left = 0
		if used < outfit.counter:
			left = outfit.counter - used
		elif outfit.prop("fission") > 0:
			fission = outfit.prop_nocharge("fission", True)
			fuel_used = int(used / fission) + 1
			if used == fuelout - s.interrupt:
				left = 0
			else:
				left = fission - used % fission
			Cargo("Uranium Fuel Cell", fuel_used).remove(s)
			Cargo("Empty Cell", fuel_used).add(s)
		elif outfit.prop("fusion") > 0:
			fusion = outfit.prop_nocharge("fusion", True)
			fuel_used = int(used / fusion) + 1
			if used == fuelout - s.interrupt:
				left = 0
			else:
				left = fusion - used % fusion
			Cargo("Hydrogen Fuel Cell", fuel_used).remove(s)
			Cargo("Empty Cell", fuel_used).add(s)
		outfit.set_counter(left)
	
	# Update if systems have not failed
	if s.interrupt != stime:
		active = stime - s.interrupt
		report.mining_interval = update_mining(s, report.mining_power, active)
		if report.assembly_rate > 0:
			update_assembly(s, report.assembly_rate, active)
		s.heat+= active * report.heat_rate
		s.energy-= (stime - gtime) * report.energy_rate
		s.shield+= active * report.shield_rate
		s.warp_charge+= active * report.warp_rate
	
	# Handle system failure
	if stime < report.now:
		for outfit in s.outfits:
			outfit.set_setting(0)
		report.energy_rate = 0
		report.heat_rate = 0
		report.shield_rate = 0
		report.warp_rate = 0
	
	# Write to database
	s.heat = max(s.heat, 0)
	s.energy = max(min(report.max_energy, s.energy), 0)
	s.shield = max(min(report.max_shield, s.shield), 0)
	if report.normal_warp > 0:
		s.warp_charge = max(min(min(report.warp_rate / report.normal_warp * report.mass, report.mass), s.warp_charge), 0)
	s.interrupt = report.now
	conn.execute("UPDATE structures SET interrupt = ?, heat = ?, energy = ?, shield = ?, warp_charge = ?, mining_progress = ? WHERE id = ?;",
		(s.interrupt, s.heat, s.energy, s.shield, s.warp_charge, s.mining_progress, s.id))
	conn.commit()
	
	return report

def set_mining_progress(s: Structure, progress: float) -> None:
	s.mining_progress = progress
	conn.execute("UPDATE structures SET mining_progress = ? WHERE id = ?;", (progress, s.id))

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


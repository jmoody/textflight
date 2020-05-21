import time
from typing import Tuple

import system
import database
import crafting
from structure import Structure
from cargo import Cargo

conn = database.conn

MAX_ASTEROID_RICHNESS = pow(2, system.ASTEROID_RICHNESS_BITS)
MINING_INTERVAL_BASE = 60

class StatusReport:
	
	mass = 0
	outfit_space = 0
	heat_rate = 0
	max_heat = 0
	energy_rate = 0
	max_energy = 0
	overheat_time = None
	powerloss_time = None
	
	shield_rate = 0
	max_shield = 0
	has_shields = False
	
	warp_rate = 0
	normal_warp = 0
	antigravity = 0
	
	electron_damage = 0
	plasma_damage = 0
	emp_damage = 0
	
	mining_power = 0
	mining_interval = 0
	assembly_rate = 0
	shipyard = 0
	
	def __init__(self):
		self.now = time.time()

def update(s: Structure) -> None:
	report = StatusReport()
	report.outfit_space = s.outfit_space
	
	# Parse outfits and cargo
	report.mass+= len(s.craft_queue)
	for cargo in s.cargo:
		try:
			report.mass+= int(cargo.extra) * cargo.count
		except:
			report.mass+= cargo.count
	for outfit in s.outfits:
		report.mass+= outfit.mark
		report.outfit_space-= outfit.mark
		
		report.antigravity+= outfit.prop("antigravity")
		report.assembly_rate+= outfit.prop("assembler")
		report.electron_damage+= outfit.prop("electron")
		report.emp_damage+= outfit.prop("emp")
		report.energy_rate+= outfit.prop("energy")
		report.heat_rate+= outfit.prop("heat")
		report.max_energy+= outfit.prop_nocharge("max_energy")
		report.max_heat+= outfit.prop_nocharge("max_heat")
		report.max_shield+= outfit.prop_nocharge("max_shield")
		report.mining_power+= outfit.prop("mining")
		report.plasma_damage+= outfit.prop("plasma")
		report.shield_rate+= outfit.prop("shield")
		report.shipyard+= outfit.prop("shipyard")
		report.warp_rate+= outfit.prop("warp")
		report.normal_warp+= outfit.prop_nocharge("warp")
		if outfit.type.properties["shield"] > 0:
			report.has_shields = True
	
	# Determine stime
	stime = report.now
	if report.heat_rate >= 0:
		if s.heat == report.max_heat:
			report.overheat_time = s.interrupt
		elif report.heat_rate > 0:
			report.overheat_time = s.interrupt + (report.max_heat - s.heat) / report.heat_rate
		if report.overheat_time != None and report.overheat_time < stime:
			stime = report.overheat_time
	if report.energy_rate >= 0:
		if s.energy == 0:
			report.powerloss_time = s.interrupt
		elif report.energy_rate > 0:
			report.powerloss_time = s.interrupt + s.energy / report.energy_rate
		if report.powerloss_time != None and report.powerloss_time < stime:
			stime = report.powerloss_time
	
	# Update if systems have not failed
	if s.interrupt != stime:
		active = stime - s.interrupt
		report.mining_interval = update_mining(s, report.mining_power, active)
		if report.assembly_rate > 0:
			update_assembly(s, stime, report.assembly_rate)
		s.heat+= active * report.heat_rate
		s.energy-= active * report.energy_rate
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
	if report.warp_rate == 0:
		s.warp_charge = 0
	
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
	interval = (MAX_ASTEROID_RICHNESS - s.system.asteroid_richness) * MINING_INTERVAL_BASE / beam_power
	count = int(elapsed / interval)
	s.mining_progress = elapsed - interval * count
	if count > 0:
		Cargo(s.system.asteroid_type.value, count).add(s)
	return interval

def update_assembly(s: Structure, stime: float, assembly_rate: float) -> float:
	for q in s.craft_queue:
		elapsed = stime - q.start
		craft_time = crafting.craft_time(q, assembly_rate)
		finished = min(q.count, int(elapsed / craft_time))
		if finished > 0:
			Cargo(q.type, finished, q.extra).add(s)
			q.start+= finished * craft_time
			q.less(finished, s)


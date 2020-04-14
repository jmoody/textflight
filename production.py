import time
from typing import Tuple

import system
import database
from structure import Structure
from cargo import Cargo

conn = database.conn

OVERHEAT = 256
MAX_ENERGY = 1024
MAX_ASTEROID_RICHNESS = pow(2, system.ASTEROID_RICHNESS_BITS)
MINING_INTERVAL_BASE = 60

class StatusReport:
	
	heat_rate = 0
	energy_rate = 0
	mining_power = 0
	mining_interval = 0
	overheat_time = None
	powerloss_time = None
	
	def __init__(self):
		self.now = time.time()

def update(s: Structure) -> None:
	report = StatusReport()
	
	# Parse outfits
	for outfit in s.outfits:
		report.energy_rate+= outfit.power_rate()
		report.heat_rate+= outfit.heat_rate()
		if outfit.type == "Mining Beam":
			report.mining_power+= outfit.operation_power()
	
	# Determine stime
	stime = report.now
	if report.heat_rate >= 0:
		if s.heat == OVERHEAT:
			report.overheat_time = s.interrupt
		else:
			report.overheat_time = s.interrupt + (OVERHEAT - s.heat) / report.heat_rate
		if report.overheat_time < stime:
			stime = report.overheat_time
	elif report.energy_rate >= 0:
		if s.energy == 0:
			report.powerloss_time = s.interrupt
		else:
			report.powerloss_time = s.interrupt + s.energy / report.energy_rate
		if report.powerloss_time < stime:
			stime = report.powerloss_time
	
	# Update to stime
	if s.interrupt != stime:
		active = stime - s.interrupt
		report.mining_interval = update_mining(s, report.mining_power, active)
		s.heat+= active * report.heat_rate
		s.energy-= active * report.energy_rate
	
	# Update to now
	if stime < report.now:
		for outfit in s.outfits:
			outfit.set_setting(0)
		report.energy_rate = 0
		report.heat_rate = 0
	
	# Write to database
	s.heat = max(min(OVERHEAT, s.heat), 0)
	s.energy = max(min(MAX_ENERGY, s.energy), 0)
	s.interrupt = report.now
	conn.execute("UPDATE structures SET heat = ?, energy = ?, interrupt = ? WHERE id = ?;", (s.heat, s.energy, s.interrupt, s.id))
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
	set_mining_progress(s, elapsed - interval * count)
	if count > 0:
		Cargo(s.system.asteroid_type.value, count).add(s)
	return interval


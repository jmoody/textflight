import time

import system
import database
from structure import Structure
from cargo import Cargo

conn = database.conn

MAX_ASTEROID_RICHNESS = pow(2, system.ASTEROID_RICHNESS_BITS)
MINING_INTERVAL_BASE = 60

def interrupt_mining(s: Structure, bonus = 0) -> None:
	interrupt = time.time() - bonus
	s.mining_interrupt = interrupt
	conn.execute("UPDATE structures SET mining_interrupt = ? WHERE id = ?", (interrupt, s.id))
	conn.commit()

def update_mining(s: Structure) -> None:
	# TODO: Handle unstable states
	beams = 0
	for outfit in s.outfits:
		if outfit.type == "Mining Beam":
			interval+= outfit.mark * oufit.op_factor()
	interval = (MAX_ASTEROID_RICHNESS - asteroid_richness) * MINING_INTERVAL_BASE / beams
	count = int((time.time() - s.mining_interrupt) / interval)
	interrupt_mining(s, count * interval)
	if count > 0:
		Cargo(s.system.asteroid_type.value, count).add(s)


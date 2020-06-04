import weakref
import time

import structure
import production
import faction
import database
import network
import config

SPAWN_SAFE = config.get_section("client").getint("SpawnSafe")

conn = database.conn

def add_target(s: structure.Structure, s2: structure.Structure) -> None:
	now = time.time()
	if now - s.created_at < SPAWN_SAFE or now - s2.created_at < SPAWN_SAFE:
		return
	s.targets.add(s2)
	s2.targets.add(s)
	if not s2 in s.tree:
		s.tree = s.tree | s2.tree
		s2.tree = s.tree
	for client in network.clients:
		if client.structure == s or client.structure == s2:
			client.tree = set(s.tree)

def clear_targets(s: structure.Structure) -> None:
	for s2 in s.targets:
		s2.targets.remove(s)
		s2.tree.remove(s)
	for client in network.clients:
		if client.structure == s:
			client.tree = set()
		elif client.structure in s.targets:
			client.tree.remove(s)
	s.targets = weakref.WeakSet()
	s.tree = weakref.WeakSet()
	s.tree.add(s)

def update_targets(sys_id: int) -> None:
	for struct in list(structure.registry.values()):
		if struct.system.id == sys_id:
			update_target(struct)

def update_target(s: structure.Structure) -> None:
	fact = faction.get_faction_by_user(s.owner_id)
	report = production.update(s)
	for stup in conn.execute("SELECT id, owner_id FROM structures WHERE sys_id = ? AND id != ?;", (s.system.id_db, s.id)):
		update_target_duo(fact, s, stup, report)

def update_target_duo(fact: faction.Faction, s: structure.Structure, stup, report) -> None:
	fact2 = faction.get_faction_by_user(stup["owner_id"])
	rep = faction.get_net_reputation(s.owner_id, fact.id, stup["owner_id"], fact2.id)
	rep = min(faction.get_net_reputation(stup["owner_id"], fact2.id, s.owner_id, fact.id), rep)
	if rep <= faction.ATTACK_MIN:
		found = False
		for t in s.targets:
			if t.id == stup["id"]:
				found = True
				break
		if not found:
			s2 = structure.load_structure(stup["id"])
			report2 = production.update(s2, report.now)
			if report.has_weapons or report2.has_weapons:
				add_target(s, s2)


import weakref

import structure
import production
import faction
import database

conn = database.conn

def add_target(s: structure.Structure, s2: structure.Structure) -> None:
	s.targets.append(s2)
	s2.targets.append(s)
	if not s2 in s.tree:
		s.tree = s.tree | s2.tree
		s2.tree = s.tree

def clear_targets(s: structure.Structure) -> None:
	for s2 in s.targets:
		s2.targets.remove(s)
		s2.tree.remove(s)
	s.targets = []
	s.tree = weakref.WeakSet()
	s.tree.add(s)

def update_targets(sys_id: int) -> None:
	for struct in list(structure.registry.values()):
		if struct.system.id == sys_id:
			update_target(struct)

def update_target(s: structure.Structure) -> None:
	fact = faction.get_faction_by_user(s.owner_id)
	report = production.update(s)
	for stup in conn.execute("SELECT id, owner_id FROM structures WHERE sys_id = ? AND id != ?;", (s.system.id, s.id)):
		update_target_duo(fact, s, stup, report.now)

def update_target_duo(fact: faction.Faction, s: structure.Structure, stup, now) -> None:
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
			production.update(s2, now)
			add_target(s, s2)


from typing import List

import database
import structure
import production

conn = database.conn

ATTACK_MIN = -1
DOCK_MIN = 1
JUMP_MIN = 2
BOARD_MIN = 3

ATTACK_PENALTY = 10
DESTROY_PENALTY = 100
CAPTURE_PENALTY = 100

class Faction:
	
	def __init__(self, ftup) -> None:
		self.id = ftup["id"]
		self.name = ftup["name"]
		self.password = ftup["password"]
		self.owner_id = ftup["owner_id"]
	
	def list_members(self) -> List[int]:
		members = []
		for i in conn.execute("SELECT username FROM users WHERE faction_id = ?;", (self.id,)):
			members.append(i["username"])
		return members
	
	def get_reputation(self, fid: int) -> int:
		rep = conn.execute("SELECT value FROM faction_reputation WHERE faction_id = ? AND faction_id2 = ?;",
			(self.id, fid)).fetchone()
		if rep == None:
			return 0
		return rep["value"]
	
	def get_user_reputation(self, uid: int, faction_dom: bool) -> int:
		rep = conn.execute("SELECT value FROM user_reputation WHERE user_id = ? AND faction_id = ? AND faction_dom = ?;",
			(uid, self.id, int(faction_dom))).fetchone()
		if rep == None:
			return 0
		return rep["value"]
	
	def set_reputation(self, fid: int, value: int) -> int:
		if value == 0:
			conn.execute("DELETE FROM faction_reputation WHERE faction_id = ? AND faction_id2 = ?;",
				(self.id, fid))
		else:
			conn.execute("INSERT INTO faction_reputation (faction_id, faction_id2, value) VALUES (?, ?, ?) ON CONFLICT(faction_id, faction_id2) DO UPDATE SET value = ?;",
				(self.id, fid, value, value))
		conn.commit()
	
	def set_user_reputation(self, uid: int, faction_dom: bool, value: int) -> int:
		if value == 0:
			conn.execute("DELETE FROM user_reputation WHERE user_id = ? AND faction_id = ? AND faction_dom = ?;",
				(uid, self.id, int(faction_dom)))
		else:
			conn.execute("INSERT INTO user_reputation (user_id, faction_id, faction_dom, value) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, faction_id, faction_dom) DO UPDATE SET value = ?;",
				(uid, self.id, int(faction_dom), value, value))
		conn.commit()

def get_faction_by_user(uid: int) -> Faction:
	ftup = conn.execute("SELECT factions.* FROM users INNER JOIN factions ON users.faction_id = factions.id WHERE users.id = ?",
		(uid,)).fetchone()
	return Faction(ftup)

def get_faction_by_name(name: str) -> Faction:
	ftup = conn.execute("SELECT * FROM factions WHERE name = ?;", (name,)).fetchone()
	if ftup == None:
		return None
	return Faction(ftup)

def get_faction(fid: int) -> Faction:
	return Faction(conn.execute("SELECT * FROM factions WHERE id = ?;", (fid,)).fetchone())

def get_personal_reputation(uid: int, uid2: int) -> int:
	rep = conn.execute("SELECT value FROM personal_reputation WHERE user_id = ? AND user_id2 = ?;",
		(uid, uid2)).fetchone()
	if rep == None:
		return 0
	return rep["value"]

def set_personal_reputation(uid: int, uid2: int, value: int) -> int:
	if value == 0:
		conn.execute("DELETE FROM personal_reputation WHERE user_id = ? AND user_id2 = ?;",
			(uid, uid2))
	else:
		conn.execute("INSERT INTO personal_reputation (user_id, user_id2, value) VALUES (?, ?, ?) ON CONFLICT(user_id, user_id2) DO UPDATE SET value = ?;",
			(uid, uid2, value, value))
	conn.commit()

def apply_penalty(uid: int, fid: int, uid2: int, penalty: int) -> None:
	if uid == uid2:
		return
	fact = get_faction_by_user(uid2)
	if fid != 0 and fact.id == fid:
		return
	prep = get_personal_reputation(uid2, uid)
	set_personal_reputation(uid2, uid, prep - penalty)
	if fact.id != 0:
		urep = fact.get_user_reputation(uid, True)
		fact.set_user_reputation(uid, True, urep - penalty)
		if fid != 0:
			rep = fact.get_reputation(fid)
			fact.set_reputation(fid, rep - penalty)
	if fid != 0:
		own = get_faction(fid)
		rep = own.get_user_reputation(uid2, False)
		own.set_user_reputation(uid2, False, rep - penalty)

def get_net_reputation(uid: int, fid: int, uid2: int, fid2: int) -> None:
	rep = get_personal_reputation(uid2, uid)
	if rep != 0:
		return rep
	fact = None
	fact2 = None
	if fid2 != 0:
		fact2 = get_faction(fid2)
		rep = fact2.get_user_reputation(uid, True)
		if rep != 0:
			return rep
	if fid != 0:
		fact = get_faction(fid)
		rep = fact.get_user_reputation(uid2, False)
		if rep != 0:
			return rep
	if fid != 0 and fid2 != 0:
		return fact2.get_reputation(fact.id)
	return 0

def has_permission(client, struct, rep_min) -> bool:
	if struct.owner_id != client.id:
		fact = get_faction_by_user(struct.owner_id)
		if fact.id == 0 or fact.id != client.faction_id:
			rep = get_net_reputation(client.id, client.faction_id, struct.owner_id, fact.id)
			if rep < rep_min:
				return False
	return True


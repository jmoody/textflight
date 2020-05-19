from typing import List

import database

conn = database.conn

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
	ftup = conn.execute("SELECT factions.* FROM users INNER JOIN factions ON users.faction_id = factions.id WHERE id = ?",
		(uid,)).fetchone()
	if ftup == None:
		return None
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


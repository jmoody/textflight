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
	
	def get_reputation(self, fid) -> int:
		rep = conn.execute("SELECT value FROM faction_reputation WHERE faction_id = ? AND faction_id2 = ?;",
			(self.id, fid)).fetchone()
		if rep == None:
			return 0
		return rep["value"]
	
	def get_user_reputation(self, uid) -> int:
		rep = conn.execute("SELECT value FROM user_reputation WHERE user_id = ? AND faction_id = ?;",
			(uid, self.id)).fetchone()
		if rep == None:
			return 0
		return rep["value"]
	
	def set_reputation(self, fid: int, value: int) -> int:
		if value == 0:
			conn.execute("DELETE FROM faction_reputation (faction_id, faction_id2) VALUES (?, ?);",
				(self.id, fid))
		else:
			conn.execute("INSERT INTO faction_reputation (faction_id, faction_id2, value) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE value = ?;",
				(self.id, fid, value, value))
		conn.commit()
	
	def set_user_reputation(self, uid: int, value: int) -> int:
		if value == 0:
			conn.execute("DELETE FROM user_reputation (user_id, faction_id) VALUES (?, ?);",
				(uid, self.id))
		else:
			conn.execute("INSERT INTO user_reputation (user_id, faction_id, value) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE value = ?;",
				(uid, self.id, value, value))
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


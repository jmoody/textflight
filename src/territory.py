from typing import Tuple

import database
from system import System

conn = database.conn

def get_system(sys: System) -> Tuple[int, str]:
	stup = conn.execute("SELECT * FROM faction_systems WHERE sys_id = ?;", (sys.id_db,)).fetchone()
	if stup != None:
		return (stup["faction_id"], stup["name"])
	return (None, None)

def get_planet(sys: System, planet_id: int) -> Tuple[int, str]:
	ptup = conn.execute("SELECT * FROM faction_planets WHERE sys_id = ? AND planet = ?;", (sys.id_db, planet_id)).fetchone()
	if ptup != None:
		return (ptup["faction_id"], ptup["name"])
	return (None, None)

def set_system(sys: System, fid: int, name: str) -> None:
	conn.execute("INSERT INTO faction_systems (sys_id, faction_id, name) VALUES (?, ?, ?) ON CONFLICT(sys_id) DO UPDATE SET faction_id = ?, name = ?;",
		(sys_id, fid, name, fid, name))
	conn.commit()

def set_planet(sys: System, planet_id: int, fid: int, name: str) -> None:
	conn.execute("INSERT INTO faction_planets (sys_id, planet, faction_id, name) VALUES (?, ?, ?, ?) ON CONFLICT(sys_id, planet) DO UPDATE SET faction_id = ?, name = ?;",
		(sys_id, planet_id, fid, name, fid, name))
	conn.commit()

def del_system(sys: System) -> None:
	conn.execute("DELETE FROM faction_systems WHERE sys_id = ?;", (sys.id_db,))
	conn.commit()

def del_planet(sys: System, planet_id: int) -> None:
	conn.execute("DELETE FROM faction_planets WHERE sys_id = ? AND planet = ?;", (sys.id_db, planet_id))
	conn.commit()


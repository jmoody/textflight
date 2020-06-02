from typing import Tuple

import database
from system import System

conn = database.conn

def get_system(sys: System) -> Tuple[int, str]:
	return get_planet(sys, None)

def get_planet(sys: System, planet_id: int) -> Tuple[int, str]:
	ptup = conn.execute("SELECT * FROM faction_claims WHERE sys_id = ? AND planet is ?;", (sys.id_db, planet_id)).fetchone()
	if ptup != None:
		return (ptup["faction_id"], ptup["name"])
	return (None, None)

def set_system(sys: System, fid: int, name: str) -> None:
	return set_planet(sys, None, fid, name)

def set_planet(sys: System, planet_id: int, fid: int, name: str) -> None:
	conn.execute("INSERT INTO faction_claims (sys_id, planet, faction_id, name) VALUES (?, ?, ?, ?) ON CONFLICT(sys_id, planet) DO UPDATE SET faction_id = ?, name = ?;",
		(sys.id_db, planet_id, fid, name, fid, name))
	conn.commit()

def del_system(sys: System) -> None:
	return del_system(sys, None)

def del_planet(sys: System, planet_id: int) -> None:
	conn.execute("DELETE FROM faction_claims WHERE sys_id = ? AND planet = ?;", (sys.id_db, planet_id))
	conn.commit()


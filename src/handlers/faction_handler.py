import logging
from typing import List

import database
import faction
import territory
import combat
import strings
import network
from client import Client

conn = database.conn

def handle_chown(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.FACTION_CHOWN)
		return
	elif c.faction_id == 0:
		c.send(strings.MISC.NOT_IN_FACTION)
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED)
		return
	utup = conn.execute("SELECT id FROM users WHERE faction_id = ? AND username = ?;",
		(fact.id, args[0])).fetchone()
	if utup == None:
		c.send(strings.FACTION.NO_MEMBER)
		return
	conn.execute("UPDATE factions SET owner_id = ? WHERE id = ?;", (utup["id"], fact.id))
	conn.commit()
	logging.info("User %d transferred ownership of faction '%s' to %d.", c.id, fact.name, utup["id"])
	c.send(strings.FACTION.NEW_OWNER, username=args[0])

def handle_claim(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	if c.structure.planet_id == None:
		fid, name = territory.get_system(c.structure.system)
		if fid == c.faction_id:
			c.send(strings.FACTION.ALREADY_CLAIMED)
			return
		rowcount = len(conn.execute("SELECT structures.id FROM structures INNER JOIN users ON users.structure_id = structures.id WHERE sys_id = ? AND faction_id != ?;",
			(c.structure.system.id_db, c.faction_id,)).fetchall())
		if rowcount > 0:
			c.send(strings.FACTION.CANNOT_CLAIM)
		else:
			territory.set_system(c.structure.system, c.faction_id, name)
			if name != None:
				c.send(strings.FACTION.CLAIMED, name=name)
			else:
				c.send(strings.FACTION.CLAIMED_SYSTEM)
	else:
		fid, name = territory.get_planet(c.structure.system, c.structure.planet_id)
		if fid == c.faction_id:
			c.send(strings.FACTION.ALREADY_CLAIMED)
			return
		rowcount = len(conn.execute("SELECT structures.id FROM structures INNER JOIN users ON users.structure_id = structures.id WHERE sys_id = ? AND faction_id != ? AND planet_id = ?;",
			(c.structure.system.id_db, c.faction_id, c.structure.planet_id)).fetchall())
		if rowcount > 0:
			c.send(strings.FACTION.CANNOT_CLAIM)
		else:
			territory.set_planet(c.structure.system, c.structure.planet_id, c.faction_id, name)
			if name != None:
				c.send(strings.FACTION.CLAIMED, name=name)
			else:
				c.send(strings.FACTION.CLAIMED_PLANET)

def handle_info(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		if c.faction_id == 0:
			c.send(strings.FACTION.NO_FACTION)
			return
		fact = faction.get_faction(c.faction_id)
	elif len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send(strings.FACTION.NO_FACTION)
			return
	else:
		c.send(strings.USAGE.FACTION_INFO)
		return
	c.send(strings.FACTION.NAME, faction_name=fact.name)
	if c.id == fact.owner_id:
		c.send(strings.FACTION.PASSWORD, faction_password=fact.password)
	owner_name = conn.execute("SELECT username FROM users WHERE id = ?;", (fact.owner_id,)).fetchone()["username"]
	c.send(strings.FACTION.OWNER, faction_owner=owner_name)
	members = fact.list_members()
	c.send(strings.FACTION.MEMBERS, count=len(members))
	for member in members:
		c.send(strings.FACTION.MEMBER, username=member)

def handle_join(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send(strings.USAGE.FACTION_JOIN)
		return
	elif not c.checkvalid(args[0]):
		c.send(strings.FACTION.ALPHANUM_ONLY)
		return
	elif c.faction_id != 0:
		c.send(strings.FACTION.ALREADY_IN_FACTION)
		return
	name = args.pop(0)
	password = " ".join(args)
	fact = faction.get_faction_by_name(name)
	if fact == None:
		c.send(strings.FACTION.CREATING_NEW)
		conn.execute("INSERT INTO factions (name, password, owner_id) VALUES (?, ?, ?);", (name, password, c.id))
		fact = faction.get_faction_by_name(name)
		logging.info("User %d created faction '%s'.", c.id, name)
	elif fact.password != password:
		c.send(strings.MISC.PERMISSION_DENIED)
		return
	c.faction_id = fact.id
	conn.execute("UPDATE users SET faction_id = ? WHERE id = ?;", (fact.id, c.id))
	conn.commit()
	c.send(strings.FACTION.JOINED, faction=name)

def handle_kick(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.FACTION_KICK)
		return
	elif c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED)
		return
	rowcount = conn.execute("UPDATE users SET faction_id = 0 WHERE faction_id = ? AND username = ? AND id != ?;",
		(fact.id, args[0], c.id)).rowcount
	if rowcount > 0:
		conn.commit()
		for client in network.clients:
			if client.username == args[0]:
				client.faction_id = 0
		c.send(strings.FACTION.KICKED, username=args[0])
	else:
		c.send(strings.FACTION.NO_MEMBER)

def handle_leave(c: Client, args: List[str]) -> None:
	fact = faction.get_faction(c.faction_id)
	members = fact.list_members()
	if fact.owner_id == c.id and len(members) > 1:
		c.send(strings.FACTION.HAS_MEMBERS)
		return
	c.faction_id = 0;
	conn.execute("UPDATE users SET faction_id = 0 WHERE id = ?;", (c.id,))
	c.send(strings.FACTION.LEFT, faction=fact.name)
	if len(members) == 1:
		conn.execute("DELETE FROM faction_claims WHERE faction_id = ?;", (fact.id,))
		conn.execute("DELETE FROM faction_reputation WHERE faction_id = ?;", (fact.id,))
		conn.execute("DELETE FROM user_reputation WHERE faction_id = ?;", (fact.id,))
		conn.execute("DELETE FROM factions WHERE id = ?;", (fact.id,))
	conn.commit()

def handle_list(c: Client, args: List[str]) -> None:
	for row in conn.execute("SELECT name FROM factions;"):
		if row["name"] == "":
			continue
		c.send(row["name"])

def handle_name(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.FACTION_NAME)
	elif not c.checkvalid(" ".join(args)):
		c.send(strings.FACTION.ALPHANUM_ONLY)
	elif c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
	elif c.structure.planet_id == None:
		fid, name = territory.get_system(c.structure.system)
		if fid == c.faction_id:
			name = " ".join(args)
			territory.set_system(c.structure.system, fid, name)
			logging.info("User %d renamed system to '%s'.", c.id, name)
			c.send(strings.FACTION.RENAMED_SYSTEM, name=name)
		else:
			c.send(strings.FACTION.NO_CLAIM)
	else:
		fid, name = territory.get_planet(c.structure.system, c.structure.planet_id)
		if fid == c.faction_id:
			name = " ".join(args)
			territory.set_planet(c.structure.system, c.structure.planet_id, fid, name)
			logging.info("User %d renamed planet to '%s'.", c.id, name)
			c.send(strings.FACTION.RENAMED_PLANET, name=name)
		else:
			c.send(strings.FACTION.NO_CLAIM)

def handle_passwd(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send(strings.USAGE.FACTION_PASSWD)
		return
	elif c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED)
	else:
		conn.execute("UPDATE factions SET password = ? WHERE id = ?;", (" ".join(args), fact.id,))
		conn.commit()
		c.send(strings.FACTION.UPDATED_PASSWORD)

def handle_release(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
	elif c.structure.planet_id == None:
		fid, name = territory.get_system(c.structure.system)
		if fid == c.faction_id:
			territory.del_system(c.structure.system)
			c.send(strings.FACTION.RELEASED_SYSTEM)
		else:
			c.send(strings.FACTION.NO_CLAIM)
	else:
		fid, name = territory.get_planet(c.structure.system, c.structure.planet_id)
		if fid == c.faction_id:
			territory.del_planet(c.structure.system, c.structure.planet_id)
			c.send(strings.FACTION.RELEASED_PLANET)
		else:
			c.send(strings.FACTION.NO_CLAIM)

def handle_rename(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send(strings.USAGE.FACTION_RENAME)
		return
	elif not c.checkvalid(args[0]):
		c.send(strings.FACTION.ALPHANUM_ONLY)
		return
	elif c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send(strings.MISC.PERMISSION_DENIED)
	else:
		conn.execute("UPDATE factions SET name = ? WHERE id = ?;", (args[0], fact.id))
		conn.commit()
		logging.info("User %d renamed faction '%s' to '%s'", fact.name, args[0])
		c.send(strings.FACTION.RENAMED, old_faction=fact.name, faction=args[0])

def handle_frepf(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	own = faction.get_faction(c.faction_id)
	if len(args) > 0 and args[0] == own.name:
		c.send(strings.FACTION.SELF_REPUTATION)
		return
	if len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send(strings.FACTION.NO_FACTION)
		else:
			c.send(strings.FACTION.REPUTATION_OF, name=fact.name, reputation=own.get_reputation(fact.id))
			c.send(strings.FACTION.REPUTATION_WITH, name=fact.name, reputation=fact.get_reputation(own.id))
	elif len(args) == 2:
		if own.owner_id != c.id:
			c.send(strings.MISC.PERMISSION_DENIED)
			return
		try:
			value = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		fact = faction.get_faction_by_name(args[0])
		if fact == None or fact.name == "":
			c.send(strings.FACTION.NO_FACTION)
		else:
			own.set_reputation(fact.id, value)
			combat.update_targets(c.structure.system.id)
			c.send(strings.FACTION.SET_REPUTATION, name=fact.name, reputation=value)
	else:
		c.send(strings.USAGE.FACTION_REPF)

def handle_repf(c: Client, args: List[str]) -> None:
	if len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send(strings.FACTION.NO_FACTION)
		elif fact.id == c.faction_id:
			c.send(strings.FACTION.SELF_REPUTATION)
		else:
			c.send(strings.FACTION.PERSONAL_REPUTATION_OF, name=fact.name, reputation=fact.get_user_reputation(c.id, False))
			c.send(strings.FACTION.PERSONAL_REPUTATION_WITH, name=fact.name, reputation=fact.get_user_reputation(c.id, True))
	elif len(args) == 2:
		try:
			value = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		fact = faction.get_faction_by_name(args[0])
		if fact == None or fact.name == "":
			c.send(strings.FACTION.NO_FACTION)
		elif fact.id == c.faction_id:
			c.send(strings.FACTION.SELF_REPUTATION)
		else:
			fact.set_user_reputation(c.id, False, value)
			combat.update_targets(c.structure.system.id)
			c.send(strings.FACTION.SET_PERSONAL_REPUTATION, name=fact.name, reputation=value)
	else:
		c.send(strings.USAGE.REPF)

def handle_rep(c: Client, args: List[str]) -> None:
	if len(args) > 0 and args[0] == c.username:
		c.send(strings.FACTION.SELF_REPUTATION)
		return
	if len(args) == 1:
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send(strings.MISC.NO_OP)
		else:
			uid = utup["id"]
			c.send(strings.FACTION.PERSONAL_REPUTATION_OF, name=args[0], reputation=faction.get_personal_reputation(c.id, uid))
			c.send(strings.FACTION.PERSONAL_REPUTATION_WITH, name=args[0], reputation=faction.get_personal_reputation(uid, c.id))
	elif len(args) == 2:
		try:
			value = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send(strings.MISC.NO_OP)
		else:
			faction.set_personal_reputation(c.id, utup["id"], value)
			combat.update_targets(c.structure.system.id)
			c.send(strings.FACTOIN.SET_PERSONAL_REPUTATION, name=args[0], reputation=value)
	else:
		c.send(strings.USAGE.REP)


def handle_frep(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send(strings.FACTION.NO_FACTION)
		return
	elif len(args) > 0 and args[0] == c.username:
		c.send(strings.FACTION.SELF_REPUTATION)
		return
	own = faction.get_faction(c.faction_id)
	if len(args) == 1:
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send(strings.MISC.NO_OP)
		else:
			uid = utup["id"]
			c.send(strings.FACTION.REPUTATION_OF, name=args[0], reputation=own.get_user_reputation(uid, True))
			c.send(strings.FACTION.REPUTATION_WITH, name=args[0], reputation=own.get_user_reputation(uid, False))
	elif len(args) == 2:
		if own.owner_id != c.id:
			c.send(strings.MISC.PERMISSION_DENIED)
			return
		try:
			value = int(args[1])
		except ValueError:
			c.send(strings.MISC.NAN)
			return
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send(strings.MISC.NO_OP)
		else:
			own.set_user_reputation(utup["id"], True, value)
			combat.update_targets(c.structure.system.id)
			c.send(strings.FACTION.SET_REPUTATION, name=args[0], reputation=value)
	else:
		c.send(strings.USAGE.FACTION_REP)


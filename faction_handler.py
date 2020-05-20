from typing import List

import database
import faction
from client import Client

conn = database.conn

def handle_chown(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: faction_chown <username>")
		return
	elif c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send("Permission denied.")
		return
	utup = conn.execute("SELECT id FROM users WHERE faction_id = ? AND username = ?;",
		(fact.id, args[0])).fetchone()
	if utup == None:
		c.send("Member does not exist.")
		return
	conn.execute("UPDATE factions SET owner_id = ? WHERE id = ?;", (utup["id"], fact.id))
	conn.commit()
	c.send("Transferred ownership of faction to '%s'.", (args[0],))

def handle_info(c: Client, args: List[str]) -> None:
	if len(args) == 0:
		if c.faction_id == 0:
			c.send("You are not in a faction.")
			return
		fact = faction.get_faction(c.faction_id)
	elif len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send("Faction does not exist.")
			return
	else:
		c.send("Usage: faction_info [faction name]")
		return
	c.send("Name: %s", (fact.name,))
	c.send("Password: %s", (fact.password,))
	owner_name = conn.execute("SELECT username FROM users WHERE id = ?;", (fact.owner_id,)).fetchone()["username"]
	c.send("Owner: %s", (owner_name,))
	members = fact.list_members()
	c.send("Members (%d):", (len(members),))
	for member in members:
		c.send("	%s", (member,))

def handle_join(c: Client, args: List[str]) -> None:
	if len(args) < 2:
		c.send("Usage: faction_join <faction name> <password>")
		return
	elif c.faction_id != 0:
		c.send("You are already in a faction.")
		return
	name = args.pop(0)
	password = " ".join(args)
	fact = faction.get_faction_by_name(name)
	if fact == None:
		c.send("Creating new faction...")
		conn.execute("INSERT INTO factions (name, password, owner_id) VALUES (?, ?, ?);", (name, password, c.id))
		fact = faction.get_faction_by_name(name)
	elif fact.password != password:
		c.send("Permission denied.")
		return
	c.faction_id = fact.id
	conn.execute("UPDATE users SET faction_id = ? WHERE id = ?;", (fact.id, c.id))
	conn.commit()
	c.send("Joined '%s'.", (name,))

def handle_kick(c: Client, args: List[str]) -> None:
	if len(args) != 1:
		c.send("Usage: faction_kick <username>")
		return
	elif c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send("Permission denied.")
		return
	rowcount = conn.execute("UPDATE users SET faction_id = 0 WHERE faction_id = ? AND username = ? AND id != ?;",
		(fact.id, args[0], c.id)).rowcount
	if rowcount > 0:
		conn.commit()
		c.send("Kicked user '%s'.", (args[0],))
	else:
		c.send("Member does not exist.")

def handle_leave(c: Client, args: List[str]) -> None:
	fact = faction.get_faction(c.faction_id)
	members = fact.list_members()
	if fact.owner_id == c.id and len(members) > 1:
		c.send("Faction still has members; kick all members or transfer ownership first.")
		return
	c.faction_id = 0;
	conn.execute("UPDATE users SET faction_id = 0 WHERE id = ?;", (c.id,))
	c.send("Left '%s'.", (fact.name,))
	if len(members) == 0:
		conn.execute("DELETE FROM factions WHERE id = ?;", (fact.id,))
	conn.commit()

def handle_list(c: Client, args: List[str]) -> None:
	for row in conn.execute("SELECT name FROM factions;"):
		if row["name"] == "":
			continue
		c.send(row["name"])

def handle_passwd(c: Client, args: List[str]) -> None:
	if len(args) < 1:
		c.send("Usage: faction_passwd <new password>")
		return
	elif c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	fact = faction.get_faction(c.faction_id)
	if fact.owner_id != c.id:
		c.send("Permission denied.")
	else:
		conn.execute("UPDATE factions SET password = ? WHERE id = ?;", (" ".join(args), fact.id,))
		conn.commit()
		c.send("Updated password.")

def handle_repf(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	own = faction.get_faction(c.id)
	if len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send("Faction does not exist.")
		else:
			c.send("Reputation of '%s': %d", (fact.name, own.get_reputation(fact.id)))
			c.send("Reputation with '%s': %d", (fact.name, fact.get_reputation(own.name)))
	elif len(args) == 2:
		if own.owner_id != c.id:
			c.send("Permission denied.")
			return
		try:
			value = int(args[1])
		except ValueError:
			c.send("Not a number.")
			return
		fact = faction.get_faction_by_name(args[0])
		if fact == None or fact.name == "":
			c.send("Faction does not exist.")
		else:
			own.set_reputation(fact.id, value)
			c.send("Set reputation of '%s' to %d.", (fact.name, value))
	else:
		c.send("Usage: repf <faction name> [value]")

def handle_repp(c: Client, args: List[str]) -> None:
	if len(args) == 1:
		fact = faction.get_faction_by_name(args[0])
		if fact == None:
			c.send("Faction does not exist.")
		else:
			c.send("Personal reputation of '%s': %d", (fact.name, fact.get_user_reputation(c.id, False)))
			c.send("Personal reputation with '%s': %d", (fact.name, fact.get_user_reputation(c.id, True)))
	elif len(args) == 2:
		try:
			value = int(args[1])
		except ValueError:
			c.send("Not a number.")
			return
		fact = faction.get_faction_by_name(args[0])
		if fact == None or fact.name == "":
			c.send("Faction does not exist.")
		else:
			fact.set_user_reputation(c.id, False, value)
			c.send("Set personal reputation of '%s' to %d.", (fact.name, value))
	else:
		c.send("Usage: repp <faction name> [value]")

def handle_rep(c: Client, args: List[str]) -> None:
	if len(args) == 1:
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send("User does not exist.")
		else:
			uid = utup["id"]
			c.send("Personal reputation of '%s': %d", (args[0], faction.get_personal_reputation(c.id, uid)))
			c.send("Personal reputation with '%s': %d", (args[0], faction.get_personal_reputation(uid, c.id)))
	elif len(args) == 2:
		try:
			value = int(args[1])
		except ValueError:
			c.send("Not a number.")
			return
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send("User does not exist.")
		else:
			faction.set_personal_reputation(c.id, utup["id"], value)
			c.send("Set personal reputation of '%s' to %d.", (args[0], value))
	else:
		c.send("Usage: rep <username> [value]")


def handle_repu(c: Client, args: List[str]) -> None:
	if c.faction_id == 0:
		c.send("You are not in a faction.")
		return
	own = faction.get_faction(c.id)
	if len(args) == 1:
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send("User does not exist.")
		else:
			uid = utup["id"]
			c.send("Reputation of '%s': %d", (args[0], own.get_user_reputation(uid, True)))
			c.send("Reputation with '%s': %d", (args[0], own.get_user_reputation(uid, False)))
	elif len(args) == 2:
		if own.owner_id != c.id:
			c.send("Permission denied.")
			return
		try:
			value = int(args[1])
		except ValueError:
			c.send("Not a number.")
			return
		utup = conn.execute("SELECT id FROM users WHERE username = ?;", (args[0],)).fetchone()
		if utup == None:
			c.send("User does not exist.")
		else:
			own.set_user_reputation(utup["id"], True, value)
			c.send("Set reputation of '%s' to %d.", (args[0], value))
	else:
		c.send("Usage: repu <username> [value]")


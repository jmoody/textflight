import sqlite3

import config

conn = sqlite3.connect(config.get_section("data").get("DatabasePath"))
conn.row_factory = sqlite3.Row
conn.cursor().execute("PRAGMA foreign_keys = ON;")

def create_table(sql: str) -> None:
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS " + sql)

create_table("""users (
	id INTEGER PRIMARY KEY,
	created_at INTEGER DEFAULT (strftime('%%s', 'now')),
	username TEXT UNIQUE NOT NULL,
	passwd TEXT NOT NULL,
	email TEXT,
	structure_id INTEGER,
	faction_id INTEGER DEFAULT 0 NOT NULL,
	chat_mode INTEGER DEFAULT 3 NOT NULL,
	language TEXT DEFAULT "%s" NOT NULL,
	premium INTEGER DEFAULT 0 NOT NULL,
	last_login INTEGER DEFAULT 0 NOT NULL,
	last_spawn INTEGER DEFAULT 0 NOT NULL,
	streak INTEGER DEFAULT 0 NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id),
	FOREIGN KEY(faction_id) REFERENCES factions(id)
);""" % (config.get_section("data").get("Language"),))

create_table("""factions (
	id INTEGER PRIMARY KEY,
	created_at INTEGER DEFAULT (strftime('%s', 'now')),
	name TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL,
	owner_id INTEGER,
	FOREIGN KEY(owner_id) REFERENCES users(id)
);""")

create_table("""faction_claims (
	sys_id INTEGER NOT NULL,
	planet INTEGER NOT NULL,
	faction_id INTEGER NOT NULL,
	name TEXT,
	FOREIGN KEY(faction_id) REFERENCES factions(id),
	PRIMARY KEY(sys_id, planet)
);""")

create_table("""faction_reputation (
	faction_id INTEGER NOT NULL,
	faction_id2 INTEGER NOT NULL,
	value INTEGER NOT NULL,
	FOREIGN KEY(faction_id) REFERENCES factions(id),
	FOREIGN KEY(faction_id2) REFERENCES factions(id),
	PRIMARY KEY(faction_id, faction_id2)
);""")

create_table("""user_reputation (
	user_id INTEGER NOT NULL,
	faction_id INTEGER NOT NULL,
	faction_dom INTEGER NOT NULL,
	value INTEGER NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id),
	FOREIGN KEY(faction_id) REFERENCES factions(id),
	PRIMARY KEY(user_id, faction_id, faction_dom)
);""")

create_table("""personal_reputation (
	user_id INTEGER NOT NULL,
	user_id2 INTEGER NOT NULL,
	value INTEGER NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id),
	FOREIGN KEY(user_id2) REFERENCES users(id),
	PRIMARY KEY(user_id, user_id2)
);""")

create_table("""structures (
	id INTEGER PRIMARY KEY,
	created_at INTEGER DEFAULT (strftime('%s', 'now')),
	name TEXT NOT NULL,
	owner_id INTEGER NOT NULL,
	type TEXT NOT NULL,
	outfit_space INTEGER NOT NULL,
	
	interrupt REAL DEFAULT 0 NOT NULL,
	heat REAL DEFAULT 0 NOT NULL,
	energy REAL DEFAULT 0 NOT NULL,
	shield REAL DEFAULT 0 NOT NULL,
	warp_charge REAL DEFAULT 0 NOT NULL,
	mining_progress REAL DEFAULT 0 NOT NULL,
	
	sys_id INTEGER NOT NULL,
	planet_id INTEGER,
	dock_id INTEGER,
	FOREIGN KEY(owner_id) REFERENCES users(id),
	FOREIGN KEY(dock_id) REFERENCES structures(id)
);""")

create_table("""outfits (
	id INTEGER PRIMARY KEY,
	type TEXT NOT NULL,
	mark INTEGER NOT NULL,
	setting INTEGER DEFAULT 0 NOT NULL,
	counter REAL DEFAULT 0 NOT NULL,
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id) ON DELETE CASCADE
);""")

create_table("""cargo (
	id INTEGER PRIMARY KEY,
	type TEXT NOT NULL,
	extra TEXT,
	count INTEGER NOT NULL,
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id) ON DELETE CASCADE
);""")

create_table("""craft_queue (
	id INTEGER PRIMARY KEY,
	type TEXT NOT NULL,
	extra TEXT,
	count INTEGER NOT NULL,
	work REAL DEFAULT 0 NOT NULL,
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id) ON DELETE CASCADE
);""")

create_table("""map (
	user_id INTEGER NOT NULL,
	sys_id INTEGER NOT NULL,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
	PRIMARY KEY (user_id, sys_id)
);""")

create_table("""keys (
	id TEXT PRIMARY KEY
);""")

try:
	conn.execute("INSERT INTO factions (id, name, password) VALUES (0, '', '');")
except sqlite3.IntegrityError:
	pass
conn.commit()

def get_user_by_username(username: str):
	c = conn.cursor()
	c.execute("SELECT id FROM users WHERE username = ?", (username,))
	return c.fetchone()


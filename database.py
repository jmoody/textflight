import sqlite3

conn = sqlite3.connect("database.db")
conn.row_factory = sqlite3.Row
conn.cursor().execute("PRAGMA foreign_keys = ON;")

def create_table(sql: str) -> None:
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS " + sql)

create_table("""users (
	id INTEGER PRIMARY KEY,
	username TEXT UNIQUE NOT NULL,
	passwd TEXT NOT NULL,
	email TEXT,
	structure_id INTEGER,
	FOREIGN KEY(structure_id) REFERENCES structures(id)
);""")

create_table("""structures (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	owner_id INTEGER,
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
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id)
);""")

create_table("""cargo (
	id INTEGER PRIMARY KEY,
	type TEXT NOT NULL,
	extra TEXT,
	count INTEGER NOT NULL,
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id)
);""")

create_table("""craft_queue (
	id INTEGER PRIMARY KEY,
	type TEXT NOT NULL,
	extra TEXT,
	count INTEGER NOT NULL,
	start REAL NOT NULL,
	structure_id INTEGER NOT NULL,
	FOREIGN KEY(structure_id) REFERENCES structures(id)
);""")

def get_user_by_username(username: str):
	c = conn.cursor()
	c.execute("SELECT id FROM users WHERE username = ?", (username,))
	return c.fetchone()


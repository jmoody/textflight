#!/usr/bin/env python3

import sys
import random
import re

import database

KEY_BITS = 128

conn = database.conn

def add_key():
	key = random.getrandbits(KEY_BITS)
	key = "{0:0{1}X}".format(key, int(KEY_BITS / 4))
	key = '-'.join(re.findall("....", key))
	if conn.execute("INSERT INTO keys (id) VALUES (?)", (key,)).rowcount > 0:
		return key
	else:
		return None

if len(sys.argv) == 1:
	for row in conn.execute("SELECT * FROM keys;"):
		print(row["id"])
elif len(sys.argv) == 2:
	count = int(sys.argv[1])
	for i in range(count):
		key = None
		while key == None:
			key = add_key()
		print(key)
	conn.commit()
else:
	print("Usage: %s [count]" % sys.argv[0])


import logging

import config
import database
from structure import Structure
from statusreport import StatusReport

conn = database.conn

def fatal_err(message: str, linenum: int) -> None:
	logging.critical("%s on line %d of quests.txt.", message, linenum)
	exit(1)

class Condition:
	pass

class ReportCondition(Condition):
	
	def __init__(self, prop: str, value: str) -> None:
		self.prop = prop
		self.value = value
	
	def is_done(self, s: Structure, report: StatusReport) -> bool:
		if self.prop == "heat_rate":
			return report.heat_rate == float(self.value)
		elif self.prop == "crew":
			return report.crew == float(self.value)
		else:
			logging.error("Unrecognized report condition '%s'.", self.prop)
			return False

class StructCondition(Condition):
	
	def __init__(self, prop: str, value: str) -> None:
		self.prop = prop
		self.value = value
	
	def is_done(self, s: Structure, report: StatusReport) -> bool:
		if self.prop == "type":
			return s.type == self.value
		else:
			logging.error("Unrecognized structure condition '%s'.", self.prop)
			return False

class SysCondition(Condition):
	
	def __init__(self, x: int, y: int) -> None:
		self.x = x
		self.y = y
	
	def is_done(self, s: Structure, report: StatusReport) -> bool:
		return s.system.x == self.x and s.system.y == self.y

class ItemCondition(Condition):
	
	def __init__(self, count: int, item: str) -> None:
		self.count = count
		self.item = item
	
	def is_done(self, s: Structure, report: StatusReport) -> bool:
		for car in s.cargo:
			if car.type == self.item:
				return car.count >= self.count
		return False

class Quest:
	
	def __init__(self, name: str, desc: str, nextq: str) -> None:
		self.name = name
		self.desc = desc
		self._next = nextq
		self.conditions = []
	
	def is_done(self, s: Structure, report: StatusReport) -> bool:
		for cond in self.conditions:
			if cond.is_done(s, report):
				return True
		return False
	
	def add(self, uid: int) -> None:
		conn.execute("INSERT INTO quests (user_id, quest) VALUES (?, ?);", (uid, self.name))
	
	def remove(self, uid: int) -> None:
		conn.execute("DELETE FROM quests WHERE user_id = ? AND quest = ?", (uid, self.name))

def get_quests(uid: int) -> None:
	ret = []
	for row in conn.execute("SELECT * FROM quests WHERE user_id = ?;", (uid,)):
		name = row["quest"]
		if not name in quests:
			logging.error("User %d has invalid quest '%s'.", uid, name)
		else:
			ret.append(quests[row["quest"]])
	return ret

quests = {}

def parse_condition(cond: str) -> None:
	args = cond.split(" ")
	typ = args.pop(0)
	if typ == "sys":
		try:
			x = int(args.pop(0))
			y = int(args.pop(0))
		except (ValueError, IndexError):
			fatal_err("Invalid number", linenum)
		conditions.append(SysCondition(x, y))
	elif typ == "item":
		try:
			count = int(args.pop(0))
		except (ValueError, IndexError):
			fatal_err("Invalid number", linenum)
		try:
			item = " ".join(args)
		except IndexError:
			fatal_err("Missing item name", linenum)
		conditions.append(ItemCondition(count, item))
	elif typ == "report":
		conditions.append(ReportCondition(args.pop(0), " ".join(args)))
	elif typ == "struct":
		conditions.append(StructCondition(args.pop(0), " ".join(args)))
	else:
		fatal_err("Invalid quest condition type '%s'" % typ, linenum)

# Parse quests from data files
linenum = 0
qname = None
desc = ""
nextq = None
conditions = []
with config.opendata("quests.txt") as f:
	for line in f:
		linenum+= 1
		tabs = len(line) - len(line.lstrip('	'))
		line = line.strip()
		if line == "":
			if qname == None:
				continue
			q = Quest(qname, desc, nextq)
			q.conditions = conditions
			quests[qname] = q
			qname = None
			desc = ""
			nextq = None
			conditions = []
		elif tabs == 0:
			if qname != None:
				fatal_err("Already parsing quest data", linenum)
			qname = line
		elif tabs == 1:
			args = line.split(" ", 1)
			cmd = args[0]
			val = args[1]
			if cmd == "description":
				desc = val
			elif cmd == "next":
				nextq = val
			elif cmd == "condition":
				parse_condition(val)
			else:
				fatal_err("Invalid quest property '%s'" % cmd, linenum)
		else:
			fatal_err("Scope error", linenum)

# Resolve quest objects
for q in quests.values():
	if q._next == None:
		continue
	elif not q._next in quests:
		logging.critical("Missing quest: '%s'.", q._next)
		exit(1)
	q.next = quests[q._next]
	logging.info("Loaded quest '%s'.", q.name)


import time
from typing import Dict

import database

conn = database.conn

class Recipe:
	has_extra = False
	
	def __init__(self, output: str, inputs: Dict[str, int]) -> None:
		self.output = output
		self.inputs = inputs

class CraftQueue:
	_rec = None
	_rec2 = None
	
	def __init__(self, ctype, count, extra = None, id = None, work = 0, structure_id = None) -> None:
		self.type = ctype
		self.extra = extra
		self.count = count
		self.id = id
		self.work = work
		self.structure_id = structure_id
	
	def add(self, s) -> None:
		for c in s.craft_queue:
			if c.type == self.type and c.extra == self.extra:
				c.count+= self.count
				conn.execute("UPDATE craft_queue SET count = ? WHERE id = ?;", (c.count, c.id))
				conn.commit()
				return
		s.craft_queue.append(self)
		self.count-= 1
		c = conn.execute("INSERT INTO craft_queue (type, extra, count, work, structure_id) VALUES (?, ?, ?, ?, ?)",
			(self.type, self.extra, self.count, self.work, s.id))
		self.id = c.lastrowid
		self.structure_id = s.id
		conn.commit()
        
	def less(self, count: int, s) -> None:
		self.count-= count
		if self.count < 1 and self.work < 0:
			s.craft_queue.remove(self)
			conn.execute("DELETE FROM craft_queue WHERE id = ?;", (self.id,))
		else:
			conn.execute("UPDATE craft_queue SET count = ?, work = ? WHERE id = ?;", (self.count, self.work, self.id))
		conn.commit()

def load_craft_queue(qtup) -> CraftQueue:
	q = CraftQueue(qtup["type"], qtup["count"], qtup["extra"], qtup["id"], qtup["work"], qtup["structure_id"])
	return q


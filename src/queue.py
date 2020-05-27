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
	
	def __init__(self, ctype, count, extra = None, id = None, start = None, structure_id = None) -> None:
		self.type = ctype
		self.extra = extra
		self.count = count
		self.id = id
		if start == None:
			self.start = time.time()
		else:
			self.start = start
		self.structure_id = structure_id
	
	def add(self, s) -> None:
		for c in s.craft_queue:
			if c.type == self.type and c.extra == self.extra:
				c.count+= self.count
				c.start = self.start
				conn.execute("UPDATE craft_queue SET count = ?, start = ? WHERE id = ?;", (c.count, c.start, c.id))
				conn.commit()
				return
		s.craft_queue.append(self)
		c = conn.execute("INSERT INTO craft_queue (type, extra, count, start, structure_id) VALUES (?, ?, ?, ?, ?)",
			(self.type, self.extra, self.count, self.start, s.id))
		self.id = c.lastrowid
		self.structure_id = s.id
		conn.commit()
        
	def less(self, count: int, s) -> None:
		self.count-= count
		if self.count < 1:
			s.craft_queue.remove(self)
			conn.execute("DELETE FROM craft_queue WHERE id = ?;", (self.id,))
		else:
			conn.execute("UPDATE craft_queue SET count = ?, start = ? WHERE id = ?;", (self.count, self.start, self.id))
		conn.commit()

def load_craft_queue(qtup) -> CraftQueue:
	q = CraftQueue(qtup["type"], qtup["count"], qtup["extra"], qtup["id"], qtup["start"], qtup["structure_id"])
	return q


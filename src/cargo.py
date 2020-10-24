import database

conn = database.conn

class Cargo:
	id = None
	structure_id = None
	
	def __init__(self, ctype, count, extra = None, theme = None, id = None, structure_id = None) -> None:
		self.type = ctype
		self.count = count
		self.extra = extra
		self.theme = theme
		self.id = id
		self.structure_id = structure_id
	
	def add(self, s) -> None:
		for c in s.cargo:
			if c.type == self.type and str(c.extra) == str(self.extra) and c.theme == self.theme:
				c.count+= self.count
				conn.execute("UPDATE cargo SET count = ? WHERE id = ?;", (c.count, c.id))
				conn.commit()
				return
		s.cargo.append(self)
		c = conn.execute("INSERT INTO cargo (type, extra, theme, count, structure_id) VALUES (?, ?, ?, ?, ?)",
			(self.type, self.extra, self.theme, self.count, s.id))
		self.id = c.lastrowid
		self.structure_id = s.id
		conn.commit()
	
	def remove(self, s) -> bool:
		for c in s.cargo:
			if c.type == self.type and str(c.extra) == str(self.extra) and c.theme == self.theme:
				c.less(self.count, s)
				return True
		return False
	
	def less(self, count: int, s) -> None:
		self.count-= count
		if self.count < 1:
			s.cargo.remove(self)
			conn.execute("DELETE FROM cargo WHERE id = ?;", (self.id,))
		else:
			conn.execute("UPDATE cargo SET count = ? WHERE id = ?;", (self.count, self.id))
		conn.commit()

def load_cargo(ctup) -> Cargo:
	cargo = Cargo(ctup["type"], ctup["count"], ctup["extra"], ctup["theme"], ctup["id"], ctup["structure_id"])
	return cargo


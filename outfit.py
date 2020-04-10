from enum import Enum

import database

conn = database.conn

class Outfit:
	
	def __init__(self, otype, mark, setting = 0, id = None, structure_id = None):
		self.type = otype
		self.mark = mark
		self.setting = setting
		self.id = id
		self.structure_id = structure_id
	
	def install(self, s) -> None:
		s.outfits.append(self)
		c = conn.execute("INSERT INTO outfits (type, mark, setting, structure_id) VALUES (?, ?, ?, ?)",
			(self.type, self.mark, self.setting, s.id))
		self.id = c.lastrowid
		self.structure_id = s.id
		conn.commit()
	
	def uninstall(self, s) -> None:
		s.outfits.remove(self)
		conn.execute("DELETE FROM outfits WHERE id = ?;", (self.id,))
		conn.commit()
	
	def set_setting(self, setting: int) -> None:
		self.setting = setting
		conn.execute("UPDATE outfits SET setting = ? WHERE id = ?;", (setting, self.id))
		conn.commit()
	
	def op_factor(self) -> float:
		return self.setting / 16

def load_outfit(otup) -> Outfit:
	outfit = Outfit(otup["type"], otup["mark"], otup["setting"], otup["id"], otup["structure_id"])
	return outfit


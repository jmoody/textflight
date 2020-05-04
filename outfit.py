from enum import Enum

import database
import cargotypes

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
		s.warp_charge = 0
		conn.execute("UPDATE structures SET warp_charge = 0 WHERE id=?;", (s.id,))
		conn.commit()
	
	def uninstall(self, s) -> None:
		s.outfits.remove(self)
		conn.execute("DELETE FROM outfits WHERE id = ?;", (self.id,))
		s.warp_charge = 0
		conn.execute("UPDATE structures SET warp_charge = 0 WHERE id=?;", (s.id,))
		conn.commit()
	
	def set_setting(self, setting: int) -> None:
		self.setting = setting
		conn.execute("UPDATE outfits SET setting = ? WHERE id = ?;", (setting, self.id))
		conn.commit()
	
	def power_rate(self) -> float:
		return cargotypes.power_rates[self.type] * self.operation_power()
	
	def heat_rate(self) -> float:
		mod = cargotypes.heat_rates[self.type]
		if self.setting <= 16:
			return mod * self.operation_power()
		elif mod > 0:
			return mod * pow(2, self.setting / 16 - 1) * self.mark
		else:
			return mod * pow(0.5, self.setting / 16 - 1) * self.mark
	
	def operation_power(self) -> float:
		return self.setting / 16 * self.mark

def load_outfit(otup) -> Outfit:
	outfit = Outfit(otup["type"], otup["mark"], otup["setting"], otup["id"], otup["structure_id"])
	return outfit


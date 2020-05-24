import database
import outfittype

conn = database.conn

class Outfit:
	
	def __init__(self, otype, mark, setting = 0, counter = 0, id = None, structure_id = None):
		self.type = outfittype.outfits[otype]
		self.mark = mark
		self.setting = setting
		self.counter = counter
		self.id = id
		self.structure_id = structure_id
	
	def install(self, s) -> None:
		s.outfits.append(self)
		c = conn.execute("INSERT INTO outfits (type, mark, setting, counter, structure_id) VALUES (?, ?, ?, ?, ?)",
			(self.type.name, self.mark, self.setting, self.counter, s.id))
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
	
	def set_counter(self, counter: int) -> None:
		self.counter = counter
		conn.execute("UPDATE outfits SET counter = ? WHERE id = ?;", (counter, self.id))
		conn.commit()
	
	def performance(self) -> float:
		return self.setting / 16 * self.mark
	
	def heat_rate(self) -> float:
		mod = self.type.properties["heat"]
		if self.setting <= 16:
			return mod * self.performance()
		else:
			return mod * pow(2, self.setting / 16 - 1) * self.mark
	
	def prop(self, key: str) -> int:
		charge = self.performance()
		if self.type.properties["overcharge"] == 0:
			charge = min(charge, self.mark)
		return self.type.properties[key] * charge
	
	def prop_nocharge(self, key: str) -> int:
		return self.type.properties[key] * self.mark

def load_outfit(otup) -> Outfit:
	outfit = Outfit(otup["type"], otup["mark"], otup["setting"], otup["counter"], otup["id"], otup["structure_id"])
	return outfit


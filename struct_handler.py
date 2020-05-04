from typing import List

import cargotypes
import production
import database
from client import Client
from cargo import Cargo
from outfit import Outfit

def handle_install(c: Client, args: List[str]):
	if len(args) != 1:
		c.send("Usage: install <cargo ID>")
		return
	try:
		cindex = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if cindex >= len(c.structure.cargo):
		c.send("Cargo does not exist.")
	else:
		cargo = c.structure.cargo[cindex]
		if not cargo.type in cargotypes.outfits:
			c.send("This is not an outfit.")
			return
		mark = int(cargo.extra)
		production.update(c.structure)
		Outfit(cargo.type, mark).install(c.structure)
		cargo.less(1, c.structure)
		c.send("Installed a mark %d '%s' from cargo.", (mark, c.translate(cargo.type)))

def handle_load(c: Client, args: List[str]):
	pass

def handle_set(c: Client, args: List[str]):
	if len(args) != 2:
		c.send("Usage: set <outfit ID> <setting>")
		return
	try:
		oindex = int(args[0])
		setting = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if oindex >= len(c.structure.outfits):
		c.send("Outfit does not exist.")
	elif setting < 0:
		c.send("Setting must be greater than zero.")
	else:
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.set_setting(setting)
		c.send("Updated setting of outfit '%s' to %d.", (c.translate(outfit.type), setting))

def handle_uninstall(c: Client, args: List[str]):
	if len(args) != 1:
		c.send("Usage: uninstall <outfit ID>")
		return
	try:
		oindex = int(args[0])
	except ValueError:
		c.send("Not a number.")
		return
	if oindex >= len(c.structure.outfits):
		c.send("Outfit does not exist.")
	else:
		outfit = c.structure.outfits[oindex]
		production.update(c.structure)
		outfit.uninstall(c.structure)
		Cargo(outfit.type, 1, str(outfit.mark)).add(c.structure)
		c.send("Uninstalled outfit '%s' into cargo.", (c.translate(outfit.type),))


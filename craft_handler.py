import time
from typing import List

import crafting
import production
from cargo import Cargo
from client import Client

def handle_cancel(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send("Usage: cancel <queue ID> <count>")
		return
	try:
		qindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if qindex >= len(c.structure.craft_queue):
		c.send("Queue does not exist.")
	else:
		c.structure.craft_queue[qindex].less(count, c.structure)
		c.send("Cancelled %d items queued for assembly.", (count,))

def handle_craft(c: Client, args: List[str]) -> None:
	production.update(c.structure)
	available = crafting.list_available(c.structure)
	if len(args) < 1:
		i = 0
		for q in available:
			c.send("[%d] %s (x%d)", (i, c.translate(q.type), q.count))
			i+= 1
	elif 1 < len(args) < 4:
		
		# Validate input
		try:
			index = int(args[0])
			count = int(args[1])
			extra = 0
			if len(args) > 2:
				extra = int(args[2])
		except ValueError:
			c.send("Not a number.")
			return
		if index >= len(available):
			c.send("Recipe does not exist.")
			return
		q = available[index]
		if q.count < count * max(1, extra):
			c.send("Not enough resources.")
			return
		elif extra == 0 and q._rec.has_extra:
			c.send("Mark not specified.")
			return
		elif extra != 0 and not q._rec.has_extra:
			c.send("Recipe has no mark options.")
			return
		
		# Remove cargo and add to queue
		for ctype in q._rec.inputs:
			Cargo(ctype, count * max(1, extra) * q._rec.inputs[ctype]).remove(c.structure)
		q.count = count
		if extra > 0:
			q.extra = extra
		q.add(c.structure)
		c.send("Queued %d items for assembly.", (count,))
		
	else:
		c.send("Usage: craft [recipe ID] [count] [mark]")

def handle_jettison(c: Client, args: List[str]) -> None:
	if len(args) != 2:
		c.send("Usage: jettison <queue ID> <count>")
		return
	try:
		cindex = int(args[0])
		count = int(args[1])
	except ValueError:
		c.send("Not a number.")
		return
	if cindex >= len(c.structure.cargo):
		c.send("Cargo does not exist.")
	else:
		c.structure.cargo[cindex].less(count, c.structure)
		c.send("Jettisoned %d items from cargo.", (count,))

def handle_queue(c: Client) -> None:
	i = 0
	report = production.update(c.structure)
	for q in c.structure.craft_queue:
		if report.assembly_rate > 0:
			elapsed = time.time() - q.start
			craft_time = crafting.craft_time(q, report.assembly_rate)
			ntime = craft_time - elapsed
			ftime = craft_time * q.count - elapsed
			time_str = "%ds/%ds" % (ntime, ftime)
		else:
			time_str = "never"
		if q.extra == None:
			c.send("[%d] %s x%d - %s", (i, c.translate(q.type), q.count, time_str))
		else:
			c.send("[%d] %s (%s) x%d - %s", (i, c.translate(q.type), q.extra, q.count, time_str))
		i+= 1


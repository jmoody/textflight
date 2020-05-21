import copy
import time
import outfittype
from math import inf
from typing import List, Dict

import system
from queue import Recipe, CraftQueue
from structure import Structure

CRAFT_TIME = 10

def load_recipes(name: str) -> Dict[str, Recipe]:
	f = open("data/%s.txt" % (name,), "r")
	out = {}
	current = None
	for line in f:
		line = line.strip()
		if line == "":
			out[current.output] = current
			current = None
		elif current == None:
			current = Recipe(line, {})
		else:
			spl = line.split(" ", 2)
			count = int(spl.pop())
			itype = " ".join(spl)
			current.inputs[itype] = count
	f.close()
	return out

def load_all_recipes() -> Dict[str, Recipe]:
	recipes = load_recipes("basic_recipes")
	
	# Load outfit recipes
	for outfit in outfittype.outfits.values():
		if outfit.recipe != None:
			recipes[outfit.name] = outfit.recipe
	
	# Load ore recipes
	for atype in system.AsteroidType:
		ore = atype.value
		ref = ore[:-4]
		recipes[ref] = Recipe(ref, {ore: 1})
	
	return recipes

def generate_craftqueues(recipes: Dict[str, Recipe]) -> List[CraftQueue]:
	craft_queues = []
	for recipe in recipes.values():
		q = CraftQueue(recipe.output, inf)
		q._rec = recipe
		q._rec2 = copy.deepcopy(recipe)
		craft_queues.append(q)
	return craft_queues

recipes = load_all_recipes()
craft_queues = generate_craftqueues(recipes)

def list_available(s: Structure) -> List[CraftQueue]:
	out = copy.deepcopy(craft_queues)
	
	# Determine maximum count of each recipe
	for cargo in s.cargo:
		for q in out.copy():
			if cargo.type in q._rec2.inputs:
				q.count = min(q.count, int(cargo.count / q._rec2.inputs[cargo.type]))
				if q.count < 1:
					out.remove(q)
					break
				del q._rec2.inputs[cargo.type]
	
	# Remove unavailable recipes
	for q in out.copy():
		q.start = time.time()
		if len(q._rec2.inputs) > 0 or q.count == inf:
			out.remove(q)
	
	return out

def craft_time(q: CraftQueue, assembly_rate: float) -> float:
	try:
		base_rate = CRAFT_TIME * int(q.extra)
	except:
		base_rate = CRAFT_TIME
	return max(1, base_rate / assembly_rate)


import copy
import time
import outfittype
from math import inf
from typing import List, Dict

import system
import config
from queue import Recipe, CraftQueue
from structure import Structure

crfc = config.get_section("crafting")
CRAFT_TIME = crfc.getint("CraftTime")
COST_FACTOR_SHIP = crfc.getfloat("CostFactorShip")
COST_FACTOR_HABITABLE = crfc.getfloat("CostFactorHabitable")
COST_FACTOR_PLANET = crfc.getfloat("CostFactorPlanet")

def load_recipes(name: str) -> List[Recipe]:
	f = config.opendata(name + ".txt")
	out = []
	current = None
	for line in f:
		line = line.strip()
		if line == "":
			out.append(current)
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

def load_all_recipes() -> List[Recipe]:
	recipes = load_recipes("basic_recipes")
	
	# Load outfit recipes
	for outfit in outfittype.outfits.values():
		if outfit.recipe != None:
			recipes.append(outfit.recipe)
	
	# Load ore recipes
	for atype in system.AsteroidType:
		ore = atype.value
		ref = ore[:-4]
		recipes.append(Recipe(ref, {ore: 1}))
	
	return recipes

def generate_craftqueues(recipes: Dict[str, Recipe]) -> List[CraftQueue]:
	craft_queues = {}
	rid = 0
	for recipe in recipes:
		q = CraftQueue(recipe.output, inf)
		q._rec = recipe
		q._rec2 = copy.deepcopy(recipe)
		craft_queues[rid] = q
		rid+= 1
	return craft_queues

recipes = load_all_recipes()
craft_queues = generate_craftqueues(recipes)

def list_available(s: Structure) -> Dict[int, CraftQueue]:
	out = copy.deepcopy(craft_queues)
	
	# Determine maximum count of each recipe
	for cargo in s.cargo:
		for rid, q in out.copy().items():
			if cargo.type in q._rec2.inputs:
				q.count = min(q.count, int(cargo.count / q._rec2.inputs[cargo.type]))
				if q.count < 1:
					del out[rid]
					continue
				del q._rec2.inputs[cargo.type]
	
	# Remove unavailable recipes
	for rid, q in out.copy().items():
		q.work = craft_time(q)
		if len(q._rec2.inputs) > 0 or q.count == inf:
			del out[rid]
	
	return out

def craft_time(q: CraftQueue) -> float:
	try:
		base_rate = CRAFT_TIME * int(q.extra)
	except:
		base_rate = CRAFT_TIME
	return base_rate


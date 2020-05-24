import sys
import copy

from queue import Recipe

class OutfitType:
	
	properties = {
		"antigravity": 0,
		"assembler": 0,
		"electron": 0,
		"emp": 0,
		"energy": 0,
		"fission": 0,
		"fusion": 0,
		"heat": 0,
		"max_energy": 0,
		"max_heat": 0,
		"max_shield": 0,
		"mining": 0,
		"plasma": 0,
		"shield": 0,
		"shipyard": 0,
		"solar": 0,
		"warp": 0,
		
		"overcharge": 1,
	}
	recipe = None
	
	def __init__(self, name: str) -> None:
		self.name = name
		self.properties = copy.deepcopy(OutfitType.properties)

class State:
	outfit = None
	linenum = 0
	recipe = False

outfits = {}
outfit_base = {
	"Light Material": 4,
	"Controller": 1,
}

# TODO: Proper logging
def fatal_err(message: str, linenum: int) -> None:
	print("%s on line %d of outfits.txt" % (message, linenum), file=sys.stderr)
	exit(1)

def add_outfit_base(recipe: Recipe) -> None:
	for itype in outfit_base:
		if itype in recipe.inputs:
			recipe.inputs[itype]+= outfit_base[itype]
		else:
			recipe.inputs[itype] = outfit_base[itype]

def handle_line(line: str, tabs: int, state: State) -> None:
	if tabs != 0 and state.outfit == None:
		fatal_err("Scope error", state.linenum)
	elif tabs == 0:
		if state.outfit != None:
			outfits[state.outfit.name] = state.outfit
			state.outfit = None
		if line != "":
			state.outfit = OutfitType(line)
			state.recipe = False
	elif tabs == 1:
		if state.recipe:
			state.recipe = False
			add_outfit_base(state.outfit.recipe)
		if line == "recipe":
			if state.outfit.recipe != None:
				fatal_err("Duplicate recipe block", state.linenum)
			state.outfit.recipe = Recipe(state.outfit.name, {})
			state.outfit.recipe.has_extra = True
			state.recipe = True
		else:
			args = line.split(" ")
			if args[0] in OutfitType.properties:
				try:
					value = float(args[1])
				except (ValueError, IndexError):
					fatal_err("Invalid number", state.linenum)
				state.outfit.properties[args[0]] = value
			else:
				fatal_err("Invalid property '%s'" % (args[0],), state.linenum)
	elif tabs == 2:
		if state.recipe:
			args = line.split(" ", 2)
			try:
				count = int(args.pop())
			except (ValueError, IndexError):
				fatal_err("Invalid recipe input", state.linenum)
			itype = " ".join(args)
			state.outfit.recipe.inputs[itype] = count
		else:
			fatal_err("Scope error", state.linenum)

with open("data/outfits.txt", "r") as f:
	state = State()
	for line in f:
		state.linenum+= 1
		tabs = len(line) - len(line.lstrip('	'))
		line = line.strip()
		if line != "" or tabs == 0:
			handle_line(line, tabs, state)


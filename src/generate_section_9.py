#!/usr/bin/env python3
import outfittype
import crafting

def print_prop(outfit, desc: str, prop: str) -> None:
	if outfit.properties[prop] != 0:
		print("\t- " + desc % outfit.properties[prop])

print("## SECTION 09: DATA FILES\n")
print("Basic materials:\n")
for recipe in crafting.recipes.values():
	if not recipe.output in outfittype.outfits:
		print("- " + recipe.output)
		mats = "\t- Materials: "
		for name, count in recipe.inputs.items():
			mats+= "%s x%d, " % (name, count)
		print(mats[:-2])

print("\nOutfits (all outfits require one Outfit Frame):\n")
for outfit in outfittype.outfits.values():
	print("- " + outfit.name)
	mats = "\t- Materials: "
	for name, count in outfit.recipe.inputs.items():
		mats+= "%s x%d, " % (name, count)
	print(mats[:-2])
	if outfit.properties["energy"] > 0:
		print("\t- Consumes %.1f energy per second." % outfit.properties["energy"])
	elif outfit.properties["energy"] < 0:
		print("\t- Generates %.1f energy per second." % -outfit.properties["energy"])
	if outfit.properties["heat"] > 0:
		print("\t- Produces %.1f heat per second." % outfit.properties["heat"])
	elif outfit.properties["heat"] < 0:
		print("\t- Cools %.1f heat per second." % -outfit.properties["heat"])
	print_prop(outfit, "Carries %d mass in antigravity field.", "antigravity")
	print_prop(outfit, "Assembles %d items per second.", "assembler")
	print_prop(outfit, "Drains %d shield per second from targets.", "electron")
	print_prop(outfit, "Drains %d energy per second from targets.", "emp")
	print_prop(outfit, "Consumes one Uranium Fuel Cell every %d seconds.", "fission")
	print_prop(outfit, "Consumes one Hydrogen Fuel Cell every %d seconds.", "fusion")
	print_prop(outfit, "Deals %d hull damage using the destroy command.", "hull")
	print_prop(outfit, "Adds capacity for %d energy.", "max_energy")
	print_prop(outfit, "Adds capacity for %d heat.", "max_heat")
	print_prop(outfit, "Adds capacity for %d shield energy.", "max_shield")
	print_prop(outfit, "Mines asteroids and collects gas. (%d)", "mining")
	print_prop(outfit, "Increases heat by %d heat per second on targets.", "plasma")
	print_prop(outfit, "Regenerates %d shield energy per second.", "shield")
	print_prop(outfit, "Allows construction of ships. (%d)", "shipyard")
	print_prop(outfit, "Generates a maximum of %d solar energy.", "solar")
	print_prop(outfit, "Generates %d warp charge per second.", "warp")


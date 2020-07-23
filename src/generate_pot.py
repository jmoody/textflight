#!/usr/bin/env python3

import inspect
import time
from typing import Set

import config
import strings
import outfittype
import crafting
import system

header = """#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: {version}\\n"
"Report-Msgid-Bugs-To: root@leagueh.xyz\\n"
"POT-Creation-Date: {creation_date}\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language: en\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
""".format(version=config.VERSION, creation_date=time.strftime("%Y-%m-%d %H:%M%z"))

def load_strings_class(output: Set[str], obj) -> None:
	for name, value in vars(obj).items():
		if not name.startswith("__"):
			output.add(value)

# Load all strings
output = set()
for name, obj in inspect.getmembers(strings):
	if inspect.isclass(obj):
		load_strings_class(output, obj)
output.update(outfittype.outfits.keys())
for recipe in crafting.recipes:
	output.add(recipe.output)
for pt in system.PlanetType:
	output.add(pt.name.lower().capitalize())
for at in system.AsteroidType:
	output.add(at.value)

# Write strings to POT file
with open("messages.pot", "w") as f:
	print(header, file=f)
	for string in output:
		print("#, python-brace-format", file=f)
		print("msgid \"%s\"" % (string,), file=f)
		print("msgstr \"\"\n", file=f)

print("Generated messages.pot with %d messages." % (len(output),))

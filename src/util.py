from typing import List

import cargo
import outfit
import client

def search_cargo(query: str, cargos: List[cargo.Cargo], c: client.Client) -> cargo.Cargo:
	try:
		cindex = int(query)
		if cindex >= len(cargos):
			return None
		return cargos[cindex]
	except ValueError:
		# TODO: Guess mark
		for car in cargos:
			if c.translate(car.type).lower().startswith(query.lower()):
				return car
		return None

def search_outfits(query: str, outfits: List[outfit.Outfit], c: client.Client) -> outfit.Outfit:
	try:
		oindex = int(query)
		if oindex >= len(outfits):
			return None
		return outfits[oindex]
	except ValueError:
		# TODO: Guess mark
		for out in outfits:
			if c.translate(out.type.name).lower().startswith(query.lower()):
				return out
		return None


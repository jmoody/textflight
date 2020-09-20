from typing import List

import cargo
import client

def search_cargo(query: str, cargos: List[cargo.Cargo], c: client.Client) -> cargo.Cargo:
	for car in cargos:
		if c.translate(car.type).lower().startswith(query.lower()):
			return car
	return None


from typing import List, Tuple

class Node:

	def __init__(self, bounds: List[Tuple[int, int]], kind: str):
		self.bounds = bounds
		self.kind = kind
	
	def python_print(self):
		raise Exception("Not implemented")
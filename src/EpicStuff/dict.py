from typing import Any

class Dict(dict):
	'''
	The class gives access to the dictionary through the attribute name.
	inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box
	'''
	def __init__(self, *args, recursive_convert=True, **kwargs) -> None:
		def handle_list(value: list) -> list:
			'''
			runs handle_dict on all (nested) elements
			:param value: list
			:return: list
			'''
			#  if value is a list, run it though this function
			if isinstance(value, list):
				value = list(map(handle_list, value))
			return handle_dict(value)
		def handle_dict(value: dict) -> dict:
			'''
			converts (nested) dicts to Dicts
			:param value: dict
			:return: dict
			'''
			if isinstance(value, dict):
				value = Dict(value)
			return value

		super().__init__(*args, **kwargs)
		# convert nested dicts to Dicts
		if recursive_convert:
			for key, value in self.items():
				self[key] = handle_list(value)
	def __getattr__(self, key: str) -> Any:
		'''
		Method returns the value of the named attribute of an object. If not found, it returns null object.
		:param name: str
		:return: Any
		'''
		return self.__getitem__(key)
	def __setattr__(self, key: str, value: Any) -> None:
		'''
		Method sets the value of given attribute of an object.
		:param key: str
		:param value: Any
		:return: None
		'''
		self.__setitem__(key, value)

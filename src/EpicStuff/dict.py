from typing import Any

class Dict(dict):
	'''
	The class gives access to the dictionary through the attribute name.
	basically copied (then simplified) from https://github.com/bstlabs/py-jdict
	'''
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		# convert nested dicts to Dicts
		for key, value in self.items():
			# TODO: maybe handle self reference
			if isinstance(value, dict):
				self[key] = Dict(value)
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

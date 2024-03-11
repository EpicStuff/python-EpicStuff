from typing import Any  # , Mapping, MutableMapping
from box import Box

class Dict(dict):
	'''
	The class gives access to the dictionary through the attribute name.
	basically copied (then simplified) from https://github.com/bstlabs/py-jdict
	'''
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

# class Dict(MutableMapping):
# 	'''basically a dictionary but you can access the keys as attributes (with a dot instead of brackets))\\
# 	you can also "bind" it to another `MutableMapping` object'''
# 	def __init__(self, target: MutableMapping | None = None) -> None:
# 		self._target = target or dict()
# 	def __getitem__(self, __key: str) -> Any:
# 		return self._target.__getitem__(__key)
# 	def __setitem__(self, __key: str, __value: Any) -> None:
# 		self._target.__setitem__(__key, __value)
# 	def __delitem__(self, __key: str) -> None:
# 		self._target.__delitem__(__key)
# 	def __iter__(self) -> Any:
# 		return self._target.__iter__()
# 	def __len__(self) -> int:
# 		return self._target.__len__()
# 	def __getattr__(self, __name: str) -> Any:
# 		if __name[0] == '_':
# 			return super().__getattribute__(__name)
# 		else:
# 			return self._target[__name]
# 	def __setattr__(self, __name: str, __value: Any) -> None:
# 		if __name[0] == '_':
# 			super().__setattr__(__name, __value)
# 		else:
# 			self._target[__name] = __value
# 	def __contains__(self, __key: object) -> bool:
# 		return self._target.__contains__(__key)
# 	def update(self, __map: Mapping = {}, overwrite=True, **kwargs) -> None:
# 		if overwrite:
# 			self._target.update(__map | kwargs)
# 		else:
# 			for key, value in (__map | kwargs).items():
# 				self._target.setdefault(key, value)

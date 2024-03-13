from typing import Any, MutableMapping, Mapping


def return_dict(*args, _convert=None, **kwargs):
	'''
	creates a new Dict
	:param args: Any
	:param _convert: bool
	:param kwargs: Any
	:return: Dict

	i know/think that is isn't "pythonic" but its the best i got
	'''
	if _convert is True or _convert is None:
		if _convert is True:
			kwargs['_convert'] = True

		class Dict(dict):
			'''
			The class gives access to the dictionary through the attribute name.
			inspired by https://github.com/bstlabs/py-jdict and https://github.com/cdgriffith/Box

			set _convert to False (`Dict()._convert=False`) to disable the conversion of (nested) dicts to Dicts if future (after initialization) values that are added
			'''

			def __init__(self, *args, recursive_convert=True, **kwargs) -> None:
				super().__init__(*args, **kwargs)
				if recursive_convert:
					for key, value in self.items():
						self[key] = self.convert(value, True)
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
			def __delattr__(self, __name: str) -> None:
				# i think, not tested
				return super().__delitem__(__name)
			def __setitem__(self, key: Any, value: Any) -> None:
				# convert value to Dict before setting
				return super().__setitem__(key, self.convert(value))
			def convert(self, value: Any, ignore__convert=False) -> Any:
				'''
				converts (nested) dicts in dicts or lists to Dicts
				:param value: Any
				:return: Any
				'''
				# if were not ignoring _convert and _convert is in self and _convert is False
				if not ignore__convert and '_convert' in self and not self._convert:
					pass
				elif isinstance(value, list):
					value = list(map(self.convert, value))
				elif isinstance(value, dict) and not isinstance(value, Dict):
					value = Dict(value)
				return value
		return Dict(*args, **kwargs)
	else:
		class Dict(MutableMapping):
			'''basically a dictionary but you can access the keys as attributes (with a dot instead of brackets))
			you can also "bind" it to another `MutableMapping` object
			
			this is the old version, for when you got a target that u dont want to convert, say for example a CommentMap'''
			def __init__(self, target: MutableMapping | None = None) -> None:
				self._t = target or dict()
			def __getitem__(self, __key: str) -> Any:
				return self._t.__getitem__(__key)
			def __setitem__(self, __key: str, __value: Any) -> None:
				self._t.__setitem__(__key, __value)
			def __delitem__(self, __key: str) -> None:
				self._t.__delitem__(__key)
			def __iter__(self) -> Any:
				return self._t.__iter__()
			def __len__(self) -> int:
				return self._t.__len__()
			def __getattr__(self, __name: str) -> Any:
				if __name[0] == '_':
					return super().__getattribute__(__name)
				else:
					return self._t[__name]
			def __setattr__(self, __name: str, __value: Any) -> None:
				if __name[0] == '_':
					super().__setattr__(__name, __value)
				else:
					self._t[__name] = __value
			def __contains__(self, __key: object) -> bool:
				return self._t.__contains__(__key)
			def update(self, __map: Mapping = {}, overwrite=True, **kwargs) -> None:
				if overwrite:
					self._t.update(__map | kwargs)
				else:
					for key, value in (__map | kwargs).items():
						self._t.setdefault(key, value)
		return Dict(*args, **kwargs)

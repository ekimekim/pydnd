from dice import roll


class Value(object):
	"""A generic object which maintains a value with self.value
	Basis of all value classes, which should always get/set with super().value
	or super().get_value(**kwargs), set_value"""
	_value = 0

	def __init__(self, value=0):
		self._value = value

	@property
	def value(self):
		return self.get_value()
	@value.setter
	def value(self, value):
		return self.set_value(value)

	def get_value(self, **kwargs):
		return self._value
	def set_value(self, value):
		self._value = value

	def __str__(self):
		return "%s(%d)" % (self.__class__.__name__, self.value)
	def __repr__(self):
		return str(self)


class Checkable(Value):
	"""Represents a value that can be rolled against with a typical d20 check."""

	def check(self, dc, bonus=0, tie_win=False, extremes=True, **kwargs):
		"""Do a check, returning bool. kwargs get passed to get_value."""
		bonus += self.get_value(**kwargs)
		return check(dc, bonus, tie_win, extrmemes)


class Overridable(Value):
	"""Represents a value that can be temporarily given a set value, masking super()'s value,
	while being able to revert back to "real" value later."""

	_mask = None

	def get_value(self, masked=True, **kwargs):
		return self._mask if masked and self._mask is not None else super(Overridable, self).get_value(**kwargs)

	def override(self, value):
		self._mask = value

	def clear_override(self):
		self._mask = None


class Bounded(Value):
	def __init__(self, min_bound=None, max_bound=None, **kwargs):
		if self.min_bound is None: self.min_bound = min_bound
		if self.max_bound is None: self.max_bound = max_bound
		super(Bounded, self).__init__(**kwargs)

	def get_value(self, bounded=True, **kwargs):
		min_bound, max_bound = self.min_bound, self.max_bound
		value = super(Bounded, self).get_value(**kwargs)
		if not bounded: return value
		assert min_bound is None or max_bound is None or min_bound <= max_bound, "Bad bounds"
		if min_bound is not None and value < min_bound: value = min_bound
		if max_bound is not None and value > max_bound: value = max_bound
		return value


class Bonusable(Value):
	"""Represents a value that can have bonuses applied.
		x = Bonusable(5)
		assert x.value == 5
		x.add_bonus("Racial", 2)
		assert x.value == 7
		assert x.get_value(exclude=['Racial']) == 5
		x.value = 7
		assert x.value == 9
	Bonuses may instead be callable, in which case they are evaluated every time get_value is called.
	Such callables should take **kwargs, which are the unknown kwargs given to get_value.
	Be careful, as this will overwrite any previous value.
	"""

	def __init__(self, **kwargs):
		self.bonuses = {}
		super(Bonusable, self).__init__(**kwargs)

	def add_bonus(self, bonus_type, value):
		old_bonus = self.bonuses.get(bonus_type, 0)
		self.bonuses[bonus_type] = value if callable(value) or callable(old_bonus) else old_bonus + value
		if not self.bonuses[bonus_type]:
			del self.bonuses[bonus_type]

	def get_value(self, exclude=[], include=None, **kwargs):
		"""Get value, excluding given bonus types. Alternately, if include given, include only these bonus types."""
		base_value = super(Bonusable, self).get_value(**kwargs)
		if include is not None:
			include = set(include).intersection(self.bonuses)
		else:
			include = set(self.bonuses) - set(exclude)
		bonuses = [self.bonuses[bonus] for bonus in include]
		bonuses = [bonus() if callable(bonus) else bonus for bonus in bonuses]
		return sum(bonuses, base_value)


class ConditionalBonusable(Bonusable):
	"""Like a Bonusable, but the semantics of the get_value args are different.
	It is designed for when most bonuses are not commonly applied, only in special circumstances.
	When you add a bonus, you may indicate whether it is on or off by default (default on).
	When you get_value, a bonus is applied if it is in defaults or include, and not in exclude.
	To disable starting from defaults, give with_defaults=False.
	"""

	def __init__(self, **kwargs):
		self.default_bonuses = set()
		super(ConditionalBonusable, self).__init__(**kwargs)

	def add_bonus(self, bonus_type, value, default=True):
		if default: self.default_bonuses.add(bonus_type)
		super(ConditionalBonusable, self).add_bonus(bonus_type, value)

	def get_value(self, exclude=[], include=[], with_defaults=True, **kwargs):
		exclude = set(exclude)
		include = set(include)
		if with_defaults:
			include |= self.default_bonuses
		include -= exclude
		return super(ConditionalBonusable, self).get_value(include=include, **kwargs)


def AbilityModified(_ability=None):
	"""Generates a value class that adds an ability score as a bonus.
	Expects a parent object containing given ability score as kwarg "parent" to __init__.
	If no ability given, must instead give "ability" to __init__.
	"""
	class _AbilityModified(Bonusable):
		def __init__(self, parent, ability=None, **kwargs):
			super(_AbilityModified, self).__init__(**kwargs)
			if not ability: ability = _ability
			assert ability, "No ability given"
			self.add_bonus(ability, lambda **kwargs: getattr(parent, ability).get_modifier(**kwargs))
	return _AbilityModified

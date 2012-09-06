from values import *


class Skill(Checkable, ConditionalBonusable, AbilityModified()):

	def __init__(self, parent, ability, synergies=[], armor_penalty=0, untrained=True, **kwargs):
		self.parent = parent
		self.synergies = synergies
		self.armor_penalty = armor_penalty
		super(Skill, self).__init__(parent=parent, ability=ability, **kwargs)

	@property
	def rank(self):
		self.get_value(with_defaults=False, synergies=False, armor_penalty=False)
	@rank.setter
	def rank(self, value):
		self.value = value

	def get_value(self, synergies=True, armor_penalty=True, **kwargs):
		value = super(Skill, self).get_value(**kwargs)
		if synergies:
			for synergy in synergies:
				if getattr(self.parent, synergy).rank >= 5:
					value += 2
		if armor_penalty and hasattr(self.parent, 'get_armor_check_penalty'):
			value -= self.armor_penalty * self.parent.get_armor_check_penalty()
		return value

	def check(self, *args, **kwargs):
		# Auto-fail if skill is trained only.
		if not self.rank:
			return False
		return super(Skill, self).check()


# TODO fill in
skill_info = [ # (name, *args for __init__)
	('spellcraft', 'int', ['knowledge_arcana'], 0, False),
	('knowledge_arcana', 'int', ['spellcraft'])
]


class HasSkills(object):
	"""This is just a bundle of skill definitions, suitable to be inherited."""

	def __init__(self, *args, **kwargs):
		super(HasSkills, self).__init__(*args, **kwargs)
		for item in skill_info:
			self.__dict__[name] = Skill(self, *item)

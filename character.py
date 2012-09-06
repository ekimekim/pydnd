from abilities import AbilityScore
from feats import feats
from dice import roll
from helpers import *
from values import *

string = str
integer = int


class AttackBonus(Checkable, ConditionalBonusable, AbilityModified('str'), AbilityModified('dex')):
	def __init__(self, **kwargs):
		super(AttackBonus, self).__init__(**kwargs)
		self.default_bonuses.remove('str')
		self.default_bonuses.remove('dex')
	def get_value(self, melee=True, ranged=False, include=set(), **kwargs):
		include = set(include)
		if ranged: include.add('dex')
		if melee: include.add('str')
		return super(AttackBonus, self).get_value(include=include, **kwargs)
class AttackDamage(ConditionalBonusable, AbilityModified('str')):
	def __init__(self, **kwargs):
		super(AttackDamage, self).__init__(**kwargs)
		self.default_bonuses.remove('str')
	def get_value(self, melee=True, include=[], **kwargs):
		include = set(include)
		if melee: include.add('str')
		return super(AttackDamage, self).get_value(include=include, **kwargs)


class TemporaryHP(Bonusable):
	"""Bonuses must not be functions."""
	sources = unique([])

	def add_bonus(self, bonus_type, *args, **kwargs):
		self.sources.append(bonus_type)
		super(TemporaryHP, self).add_bonus(bonus_type, *args, **kwargs)
	def damage(self, amount):
		"""Deal amount to temporary hp. Returns amount that wasn't absorbable."""
		while amount and self.sources:
			if amount >= self.sources[0]:
				amount -= self.bonuses.pop(self.sources.pop(0))
			else:
				self.bonuses[self.sources[0]] -= amount
				amount = 0
		return amount


class MaxHP(Bounded, AbilityModified('con')):
	min_bound = 1
	def __init__(self, parent, **kwargs):
		super(MaxHP, self).__init__(parent=parent, **kwargs)
		# Replace con bonus with level * con bonus
		get_con = self.bonuses['con']
		self.add_bonus('con', lambda **kwargs: parent.level * get_con(**kwargs))


class Character(HasSkills):

	class_levels = unique({})
	_race = None
	feats = unique([])
	max_hp = with_parent(MaxHP)
	_damage = 0

	str = unique(AbilityScore)
	dex = unique(AbilityScore)
	con = unique(AbilityScore)
	int = unique(AbilityScore)
	wis = unique(AbilityScore)
	cha = unique(AbilityScore)

	replay_log = unique([])

	initiative = with_parent(from_bases(Checkable, AbilityModified('dex')))
	attack = with_parent(AttackBonus)
	attack_damage = with_parent(AttackDamage)

	temporary_hp = unique(TemporaryHP)

	def __init__(self, race, (str,dex,con,int,wis,cha), hd_mode=('random','normal')):
		"""hd_mode: 2-tuple. first part may be 'random' or 'average', governing how hd are calculated.
		second part may be 'normal', 'bonus', governing if first hd is always full.
		"""
		super(Character, self).__init__(self)
		self.str.value = str
		self.dex.value = dex
		self.con.value = con
		self.int.value = int
		self.wis.value = wis
		self.cha.value = cha
		self.race = race
		self.hd_mode = hd_mode

	@property
	def race(self):
		return self._race
	@race.setter
	def race(self, value):
		if self._race is not None: self._race.unapply(self)
		self._race = value
		value.apply(self)

	@property
	def level(self):
		return sum(self.class_levels.values())

	@property
	def damage(self):
		return self._damage
	@damage.setter
	def damage(self, value):
		self._damage = max(0, value)
		self.check_hp()

	@property
	def hp(self):
		return self.max_hp.value - self.damage

	def check_hp(self):
		pass # TODO

	def ask(self, prompt, question_callback, answer_callback):
		"""answer callback takes arg answer and returns error message or None for success.
		This func returns successful answer."""
		error = ''
		while 1:
			answer = question_callback(error + prompt)
			error = answer_callback(answer)
			if error is None:
				self.replay_log.append(answer)
				return answer
			error += '\n'

	def level_up(self, next_class, question_callback):
		"""callback takes arg question and returns string answer"""

		# Increment level
		self.class_levels[next_class] = self.class_levels.get(next_class, 0) + 1
		next_class.apply_level(self.class_levels[next_class], question_callback)
		# Race hook
		self.race.on_level_up(self)
		# Give ability point
		if self.level % 4 == 0:
			ability = self.ask("Increase an ability score", question_callback,
			                   lambda answer: None if ability in ('str', 'dex', 'con', 'int', 'wis', 'cha') else "Bad ability"
			getattr(self, ability).add_bonus("from level", 1)
		# Choose new feat
		if self.level % 3 == 0 or self.level == 1:
			def pick_feat(answer):
				try:
					feat = feats[feat_s]
					feat.apply(self)
					self.feats.append(feat)
				except KeyError:
					return 'Unknown feat'
				except RequirementsError, ex:
					return string(ex)
			self.ask("Feat?", question_callback, answer_callback)
		# Choose new skills
		self.skill_points += (next_class.skill_points + self.int.get_true_modifier()) * (4 if level == 1 else 1)
		def pick_skill(skill_s):
			if skill_s == 'done': return
			if not hasattr(self, skill_s):
				return "Unknown skill"
			skill = getattr(self, skill_s)
			if not isinstance(skill, Skill):
				return 'Unknown skill'
			crossclass = not any(skill_s in c.skills for c in self.class_levels.values())
			max_ranks = (self.level + 3) / 2 - skill.ranks if crossclass else self.level + 3 - skill.ranks
			max_ranks = min(max_ranks, self.skill_points / 2 if crossclass else self.skill_points)
			def pick_ranks(num):
				if num == 'cancel': return
				try:
					num = integer(num)
				except ValueError:
					return 'Not a valid integer'
				if num > max_ranks:
					return "Too many ranks"
			num = self.ask("(%s) How many ranks? (Up to %d) ('cancel' to cancel)" % ('cross-class skill' if crossclass else 'class skill'), max_ranks),
			               question_callback, pick_ranks)
			if num == 'cancel': return ''
			num = int(num)
			self.skill_points -= num if crossclass else num * 2
			skill.ranks += num
		while 1:
			skill = ask("Rank up skill (or 'done')? (%d points remaining)" % self.skill_points, question_callback, pick_skill)
			if skill == 'done':
				break
		# Update hp
		hd = next_level.hd
		hd = self.race.hd_hook(self, hd)
		style, bonus = self.hd_mode
		if level == 1 and bonus == 'bonus':
			hp = hd
		else:
			hp = roll(1, hd)
		hp = max(hp, 1)
		self.max_hp += hp

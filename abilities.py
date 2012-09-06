from values import *
from dice import check

class AbilityScore(Bounded, Overridable, Bonusable):
	min_bound = 0

	def get_modifier(self, **kwargs):
		value = self.get_value(**kwargs)
		return int(value/2 - 5)
	modifier = property(get_modifier)
	mod = modifier

	def get_true_value(self):
		return self.get_value(include=['racial', 'from level'], masked=False)

	def get_true_modifier(self):
		return self.get_modifier(include=['racial', 'from level'], masked=False)

	def get_point_cost(self):
		LUT = {8:0, 9:1, 10:2, 11:3, 12:4, 13:5, 14:6, 15:8, 16:10, 17:13, 18:16}
		value = self.get_value(include=[])
		return LUT[value]

	def check(self, dc, bonus=0, tie_win=False, extremes=True, **kwargs):
		bonus += self.get_modifier(**kwargs)
		return check(dc, bonus, tie_win, extremes)

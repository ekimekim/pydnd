import re

try:
	import quantumrandom
	generator = quantumrandom.cached_generator()
	get_int = lambda n: quantumrandom.randint(1, n, generator)
except ImportError:
	import random
	get_int = lambda n: random.randint(1, n)


def roll(n, sides, bonus=0):
	return sum([get_int(sides) for i in xrange(n)], bonus)


pattern = re.compile(r'^([0-9]*)d([0-9]+)(?:\+([0-9]+))?')
def rollstr(s):
	match = pattern.match(s)
	if not match:
		raise ValueError("Badly formatted roll string: %s" % s)
	n, sides, bonus = match.groups
	if not n: n = 0
	if not bonus: bonus = 0	
	return roll(int(n), int(sides), int(bonus))


def check(dc, bonus=0, tie_win=False, extremes=True):
	raw_result = roll(1, 20, 0)
	if extremes and raw_result in (1, 20): return raw_result == 20
	result += bonus
	return result > dc or (tie_win and result == dc)


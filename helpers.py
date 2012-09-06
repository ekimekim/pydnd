import itertools as it


def from_bases(*bases):
	return type(','.join(bases), bases, {})


def get_resolved_dict(instance):
	"""Returns a fully-resolved __dict__ for an object."""
	d = {}
	for cls in reversed(instance.__class__.mro()):
		d.update(cls.__dict__)
	d.update(instance.__dict__)
	return d


def with_parent(cls, callback=None):
	"""Use this to wrap a class and assign it to a class attribute.
	On first access, it will replace itself with an instance of cls,
	passing parent=<the class it is an attribute of> to __init__.
	Or instead you can provide your own callback, which takes the
	args (cls, parent) and returns the object to replace the original wrapper with.
	Note: This will not work if the wrapped value is masked by instance variables or other
	classes before it in the mro.
	"""
	class _with_parent_wrapper(object):
		def __get__(self, parent, parent_cls):
			if not callback: callback = lambda cls, parent: cls(parent=parent)
			replacement = callback(cls, parent)
			for k, v in get_resolved_dict(parent).items():
				if isinstance(v, _with_parent_wrapper):
					setattr(parent, k, replacement)
	return _with_parent_wrapper()


def unique(cls, *args, **kwargs):
	"""A simpler version of with_parent, drops the parent kwarg. If not given a class,
	will use type(obj) instead.
	args and kwargs get passed through to the __init__."""
	return with_parent(cls if isinstance(cls, type) else type(cls), callback = lambda cls, parent: cls(*args, **kwargs))

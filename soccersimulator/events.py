# -*- coding: utf-8 -*-

class Events(object):
    def __init__(self):
        for e in self.__events__:
            self.__getattr__(e)

    def __getattr__(self, name):
        if hasattr(self.__class__, '__events__'):
            assert name in self.__class__.__events__, \
                "Event '%s' is not declared" % name
        self.__dict__[name] = ev = _EventSlot(name)
        return ev

    def __str__(self):
        return 'Events :' + str(list(self))

    __repr__ = __str__

    def __len__(self):
        if len(self.__dict__) != 0:
            return len(self.__dict__.values()[0])
        return 0

    def __iter__(self):
        def gen(dictitems=self.__dict__.items()):
            for attr, val in dictitems:
                if isinstance(val, _EventSlot):
                    yield val

        return gen()

class _EventSlot(object):
    def __init__(self, name):
        self.targets = []
        self.__name__ = name

    def __repr__(self):
        return self.__name__

    def __call__(self, *a, **kw):
        return [f(*a, **kw) for f in self.targets]

    def __iadd__(self, f):
        self.targets.append(f)
        return self

    def __isub__(self, f):
        while f in self.targets: self.targets.remove(f)
        return self

    def __len__(self):
        return len(self.targets)


class SoccerEvents(Events):
    __events__ = ('begin_match', 'begin_round', 'update_round', 'end_round', 'end_match', 'is_ready','send_strategy')
    def __iadd__(self, f):
        for e in self:
            try:
                e += getattr(f, str(e))
            except:
                pass
        return self

    def __isub__(self, f):
        for e in self:
            try:
                while getattr(f, str(e)) in e.targets: e.targets.remove(getattr(f, str(e)))
            except:
                pass
        return self

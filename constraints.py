import numpy as np
import features

class Constraint:
    def __init__(self, system=None):
        self.system = system
        self._variables = tuple()
        self._features = tuple()

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, value):
        assert isinstance(value, tuple), ValueError("features must be tuple")

        for f in self._features:
            f.constraints.remove(self)
        self._features = value
        for f in self._features:
            f.constraints.append(self)

    @property
    def variables(self):
        return self._variables

    @variables.setter
    def variables(self, value):
        assert isinstance(value, tuple), ValueError("variables must be tuple")
        self._variables = value

    @classmethod
    def assert_compatible(cls, args):
        assert cls.compatible(args), ValueError("{} is not available for the given features")

    @classmethod
    def compatible(cls, fs):
        return False

    def __str__(self):
        return "{}".format(self.__class__.__name__)

def line_or_two_points(fs):
    return (len(fs) == 1 and
            isinstance(fs[0], features.Line) or
            len(fs) == 2 and
            isinstance(fs[0], features.Point) and
            isinstance(fs[1], features.Point))

def two_lines(fs):
    return (len(fs) == 2 and
            isinstance(fs[0], features.Line) and
            isinstance(fs[1], features.Line))

class FixedDistance(Constraint):
    def __init__(self, p1, p2, dist, **kwargs):
        super().__init__(**kwargs)
        self.dist = dist
        self.p1 = p1
        self.p2 = p2
        self.features = (self.p1, self.p2)
        self.variables = (self.p1.x, self.p1.y, self.p2.x, self.p2.y)

    def f(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        return lambda x: np.array([(x[p2x] - x[p1x]) ** 2 + (x[p2y] - x[p1y]) ** 2 - self.dist ** 2])

    def df(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, p1x] = -2 * (x[p2x] - x[p1x])
            p[0, p1y] = -2 * (x[p2y] - x[p1y])
            p[0, p2x] = 2 * (x[p2x] - x[p1x])
            p[0, p2y] = 2 * (x[p2y] - x[p1y])
            return p
        return _df

class Distance:
    def __init__(self, p1, p2, dist, **kwargs):
        super().__init__(**kwargs)
        self.dist = dist
        self.p1 = p1
        self.p2 = p2
        self.variables = (p1.x, p1.y, p2.x, p2.y, dist)

    def f(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        d = variables[self.dist]
        return lambda x: np.array([(x[p2x] - x[p1x]) ** 2 + (x[p2y] - x[p1y]) ** 2 - x[d] ** 2])

    def df(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        d = variables[self.dist]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, p1x] = -2 * (x[p2x] - x[p1x])
            p[0, p1y] = -2 * (x[p2y] - x[p1y])
            p[0, p2x] = 2 * (x[p2x] - x[p1x])
            p[0, p2y] = 2 * (x[p2y] - x[p1y])
            p[0, d] = -2 * x[d]
            return p
        return _df

class Fixed:
    def __init__(self, var, val, **kwargs):
        super().__init__(**kwargs)
        self.var = var
        self.val = val
        self.variables = (self.var,)

    def f(self, variables):
        v = variables[self.var]
        return lambda x: np.array([x[v] - self.val])

    def df(self, variables):
        v = variables[self.var]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, v] = 1
            return p
        return _df

class Equal:
    def __init__(self, var1, var2, **kwargs):
        super().__init__(**kwargs)
        self.var1 = var1
        self.var2 = var2
        self.variables = (var1, var2)

    def f(self, variables):
        v1 = variables[self.var1]
        v2 = variables[self.var2]
        return lambda x: np.array(x[v1] - x[v2])

    def df(self, variables):
        v1 = variables[self.var1]
        v2 = variables[self.var2]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, v1] = 1
            p[0, v2] = -1
            return p
        return _df

class FixedX(Fixed, Constraint):
    def __init__(self, point, val, **kwargs):
        super().__init__(point.x, val, **kwargs)
        self.features = (point,)

class FixedY(Fixed, Constraint):
    def __init__(self, point, val, **kwargs):
        super().__init__(point.y, val, **kwargs)
        self.features = (point,)

class Vertical(Equal, Constraint):
    def __init__(self, *args, **kwargs):
        self.assert_compatible(args)
        if len(args) == 2:
            (p1, p2) = args
            super().__init__(p1.x, p2.x, **kwargs)
            self.features = (p1, p2)
        elif len(args) == 1:
            (l,) = args
            super().__init__(l.p1.x, l.p2.x, **kwargs)
            self.features = (l,)

    @classmethod
    def compatible(cls, fs):
        return line_or_two_points(fs)

class Horizontal(Equal, Constraint):
    def __init__(self, *args, **kwargs):
        self.assert_compatible(args)
        if len(args) == 2:
            (p1, p2) = args
            super().__init__(p1.y, p2.y, **kwargs)
            self.features = (p1, p2)
        elif len(args) == 1:
            (l,) = args
            super().__init__(l.p1.y, l.p2.y, **kwargs)
            self.features = (l,)

    @classmethod
    def compatible(cls, fs):
        return line_or_two_points(fs)

class CongruentLines(Constraint):
    def __init__(self, *args, **kwargs):
        self.assert_compatible(args)
        (l1, l2) = args
        super().__init__(**kwargs)
        self.l1 = l1
        self.l2 = l2
        self.features = (l1, l2)
        self.variables = (l1.p1.x, l1.p1.y, l1.p2.x, l1.p2.y,
                          l2.p1.x, l2.p1.y, l2.p2.x, l2.p2.y)

    @classmethod
    def compatible(cls, fs):
        return two_lines(fs)

    def f(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        return lambda x: np.array([(x[l1p2x] - x[l1p1x]) ** 2 + (x[l1p2y] - x[l1p1y]) ** 2 - (x[l2p2x] - x[l2p1x]) ** 2 - (x[l2p2y] - x[l2p1y]) ** 2])

    def df(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, l1p1x] = -2 * (x[l1p2x] - x[l1p1x])
            p[0, l1p1y] = -2 * (x[l1p2y] - x[l1p1y])
            p[0, l1p2x] =  2 * (x[l1p2x] - x[l1p1x])
            p[0, l1p2y] =  2 * (x[l1p2y] - x[l1p1y])
            p[0, l2p1x] =  2 * (x[l2p2x] - x[l2p1x])
            p[0, l2p1y] =  2 * (x[l2p2y] - x[l2p1y])
            p[0, l2p2x] = -2 * (x[l2p2x] - x[l2p1x])
            p[0, l2p2y] = -2 * (x[l2p2y] - x[l2p1y])
            return p
        return _df

class Parallel(Constraint):
    def __init__(self, *args, **kwargs):
        self.assert_compatible(args)
        (l1, l2) = args
        super().__init__(**kwargs)
        self.l1 = l1
        self.l2 = l2
        self.features = (l1, l2)
        self.variables = (l1.p1.x, l1.p1.y, l1.p2.x, l1.p2.y,
                          l2.p1.x, l2.p1.y, l2.p2.x, l2.p2.y)

    @classmethod
    def compatible(cls, fs):
        return two_lines(fs)

    def f(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        return lambda x: np.array([(x[l1p2x] - x[l1p1x]) * (x[l2p2y] - x[l2p1y]) - (x[l1p2y] - x[l1p1y]) * (x[l2p2x] - x[l2p1x])])

    def df(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, l1p1x] = -(x[l2p2y] - x[l2p1y])
            p[0, l1p1y] = -(x[l2p2x] - x[l2p1x])
            p[0, l1p2x] =  (x[l2p2y] - x[l2p1y])
            p[0, l1p2y] =  (x[l2p2x] - x[l2p1x])
            p[0, l2p1x] =  (x[l1p2y] - x[l1p1y])
            p[0, l2p1y] =  (x[l1p2x] - x[l1p1x])
            p[0, l2p2x] = -(x[l1p2y] - x[l1p1y])
            p[0, l2p2y] = -(x[l1p2x] - x[l1p1x])
            return p
        return _df

class Perpendicular(Constraint):
    def __init__(self, *args, **kwargs):
        self.assert_compatible(args)
        (l1, l2) = args
        super().__init__(**kwargs)
        self.l1 = l1
        self.l2 = l2
        self.features = (l1, l2)
        self.variables = (l1.p1.x, l1.p1.y, l1.p2.x, l1.p2.y,
                          l2.p1.x, l2.p1.y, l2.p2.x, l2.p2.y)

    @classmethod
    def compatible(cls, fs):
        return two_lines(fs)

    def f(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        return lambda x: np.array([(x[l1p2x] - x[l1p1x]) * (x[l2p2x] - x[l2p1x]) + (x[l1p2y] - x[l1p1y]) * (x[l2p2y] - x[l2p1y])])

    def df(self, variables):
        l1p1x = variables[self.l1.p1.x]
        l1p1y = variables[self.l1.p1.y]
        l1p2x = variables[self.l1.p2.x]
        l1p2y = variables[self.l1.p2.y]
        l2p1x = variables[self.l2.p1.x]
        l2p1y = variables[self.l2.p1.y]
        l2p2x = variables[self.l2.p2.x]
        l2p2y = variables[self.l2.p2.y]
        def _df(x):
            p = np.zeros((1, len(variables)))
            p[0, l1p1x] = -(x[l2p2x] - x[l2p1x])
            p[0, l1p1y] = -(x[l2p2y] - x[l2p1y])
            p[0, l1p2x] =  (x[l2p2x] - x[l2p1x])
            p[0, l1p2y] =  (x[l2p2y] - x[l2p1y])
            p[0, l2p1x] = -(x[l1p2x] - x[l1p1x])
            p[0, l2p1y] = -(x[l1p2y] - x[l1p1y])
            p[0, l2p2x] =  (x[l1p2x] - x[l1p1x])
            p[0, l2p2y] =  (x[l1p2y] - x[l1p1y])
            return p
        return _df



available = (
    Vertical,
    Horizontal,
    CongruentLines,
    Parallel,
    Perpendicular
)

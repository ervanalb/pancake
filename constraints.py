import numpy as np

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
        self.features = (self.var,)
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

class FixedX(Constraint, Fixed):
    def __init__(self, point, val, **kwargs):
        super().__init__(point.x, val, **kwargs)
        self.features = (self.point,)

class FixedY(Constraint, Fixed):
    def __init__(self, point, val, **kwargs):
        super().__init__(point.y, val, **kwargs)
        self.features = (self.point,)

class Vertical(Equal, Constraint):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(p1.x, p2.x, **kwargs)
        self.features = (p1, p2)

class Horizontal(Equal, Constraint):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(p1.y, p2.y, **kwargs)
        self.features = (p1, p2)

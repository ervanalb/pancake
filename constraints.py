import numpy as np

class FixedDistance:
    def __init__(self, p1, p2, dist):
        self.dist = dist
        self.p1 = p1
        self.p2 = p2

    @property
    def variables(self):
        return [self.p1.x, self.p1.y, self.p2.x, self.p2.y]

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
    def __init__(self, p1, p2, dist):
        self.dist = dist
        self.p1 = p1
        self.p2 = p2

    @property
    def variables(self):
        return [self.p1.x, self.p1.y, self.p2.x, self.p2.y, self.dist]

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
    def __init__(self, var, val):
        self.var = var
        self.val = val

    @property
    def variables(self):
        return [self.var]

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
    def __init__(self, var1, var2):
        self.var1 = var1
        self.var2 = var2

    @property
    def variables(self):
        return [self.var1, self.var2]

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

class FixedX(Fixed):
    def __init__(self, p, x):
        super().__init__(p.x, x)

class FixedY(Fixed):
    def __init__(self, p, y):
        super().__init__(p.y, y)

class Vertical(Equal):
    def __init__(self, p1, p2):
        super().__init__(p1.x, p2.x)

class Horizontal(Equal):
    def __init__(self, p1, p2):
        super().__init__(p1.y, p2.y)

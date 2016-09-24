import numpy as np

class Variable:
    def __init__(self, value, name=None):
        self.value = float(value)
        self.name = name

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)

    def __str__(self):
        if self.name is not None:
            return "{} = {}".format(self.name, self.value)
        return str(self.value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self))

class Point:
    def __init__(self, x, y, name=None):
        self.x = Variable(x, "{}.x".format(name) if name is not None else None)
        self.y = Variable(y, "{}.y".format(name) if name is not None else None)
        self.name = name

    def __str__(self):
        if self.name is not None:
            return "{} = ({}, {})".format(self.name, self.x.value, self.y.value)
        return "({}, {})".format(self.x.value, self.y.value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self))

class FixedDistance:
    def __init__(self, p1, p2, dist):
        self.dist = dist
        self.p1 = p1
        self.p2 = p2

    @property
    def variables(self):
        return {self.p1.x, self.p1.y, self.p2.x, self.p2.y}

    def f(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        return lambda x: (x[p2x] - x[p1x]) ** 2 + (x[p2y] - x[p1y]) ** 2 - self.dist ** 2

    def df(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        def _df(x):
            p = np.zeros(len(variables))
            p[p1x] = -2 * (x[p2x] - x[p1x])
            p[p1y] = -2 * (x[p2y] - x[p1y])
            p[p2x] = 2 * (x[p2x] - x[p1x])
            p[p2y] = 2 * (x[p2y] - x[p1y])
            return p
        return _df

class Distance:
    def __init__(self, p1, p2, dist):
        self.dist = dist
        self.p1 = p1
        self.p2 = p2

    @property
    def variables(self):
        return {self.p1.x, self.p1.y, self.p2.x, self.p2.y, self.dist}

    def f(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        d = variables[self.dist]
        return lambda x: (x[p2x] - x[p1x]) ** 2 + (x[p2y] - x[p1y]) ** 2 - x[d] ** 2

    def df(self, variables):
        p1x = variables[self.p1.x]
        p1y = variables[self.p1.y]
        p2x = variables[self.p2.x]
        p2y = variables[self.p2.y]
        d = variables[self.dist]
        def _df(x):
            p = np.zeros(len(variables))
            p[p1x] = -2 * (x[p2x] - x[p1x])
            p[p1y] = -2 * (x[p2y] - x[p1y])
            p[p2x] = 2 * (x[p2x] - x[p1x])
            p[p2y] = 2 * (x[p2y] - x[p1y])
            p[d] = -2 * x[d]
            return p
        return _df

class Fixed:
    def __init__(self, var, val):
        self.var = var
        self.val = val

    @property
    def variables(self):
        return {self.var}

    def f(self, variables):
        v = variables[self.var]
        return lambda x: x[v] - self.val

    def df(self, variables):
        v = variables[self.var]
        def _df(x):
            p = np.zeros(len(variables))
            p[v] = 1
            return p
        return _df

class Equal:
    def __init__(self, var1, var2):
        self.var1 = var1
        self.var2 = var2

    @property
    def variables(self):
        return {self.var1, self.var2}

    def f(self, variables):
        v1 = variables[self.var1]
        v2 = variables[self.var2]
        return lambda x: x[v1] - x[v2]

    def df(self, variables):
        v1 = variables[self.var1]
        v2 = variables[self.var2]
        def _df(x):
            p = np.zeros(len(variables))
            p[v1] = 1
            p[v2] = -1
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

EPSILON = 0
MAX_ITER = 100

def solve(eqs):
    variables_list = [v for eq in eqs for v in eq.variables]

    # Remove duplicates preserving order (for deterministic results)
    seen = set()
    seen_add = seen.add
    variables_list = [x for x in variables_list if not (x in seen or seen_add(x))]

    variables_dict = {v: i for i, v in enumerate(variables_list)}
    x = np.array([v.value for v in variables_list])
    f = lambda x: np.array([e.f(variables_dict)(x) for e in eqs])
    df = lambda x: np.vstack([e.df(variables_dict)(x) for e in eqs])
    for i in range(MAX_ITER):
        f_x = f(x)
        if np.all(np.abs(f_x) <= EPSILON):
            print("Converged in {} iters".format(i))
            break
        dx = np.dot(np.linalg.pinv(df(x)), -f_x)
        x += dx
    else:
        raise Exception("Did not converge.")

    for (xv, v) in zip(x, variables_list):
        v.value = xv

d = Variable(10, "d")
pa = Point(0, 0, "pa")
pb = Point(1, 0, "pb")
pc = Point(1, 1, "pc")

c = [FixedX(pa, 0),
     FixedY(pa, 0),
     Horizontal(pa, pb),
     Distance(pa, pb, d),
     Distance(pa, pc, d),
     Distance(pb, pc, d)]

np.set_printoptions(suppress=True)
solve(c)
print(pa, pb, pc, d)

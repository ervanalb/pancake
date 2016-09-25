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

EPSILON = 1e-10
MAX_ITER = 100

def remove_duplicates(l):
    seen = set()
    seen_add = seen.add
    return [x for x in l if not (x in seen or seen_add(x))]

def solve(eqs):
    # Convert the given equations into a mapping of variables to equations
    variables_to_eqs = {}

    for e in eqs:
        for v in e.variables:
            if v in variables_to_eqs:
                variables_to_eqs[v].add(e)
            else:
                variables_to_eqs[v] = {e}

    # Perform depth-first search to find connected components

    eqs_unseen = eqs[:]

    def search(eq):
        if eq not in eqs_unseen:
            return
        eqs_unseen.remove(eq)
        eqs_in_component.append(eq)
        connected = remove_duplicates([neq for var in eq.variables for neq in variables_to_eqs[var]])
        for neq in connected:
            search(neq)

    # Enumerate all components

    components = []

    while len(eqs_unseen) > 0:
        eqs_in_component = []
        search(eqs_unseen[0])
        components.append(eqs_in_component)

    # Solve each component independently
    for component in components:
        # Get a list of variables
        variables_list = remove_duplicates([v for eq in component for v in eq.variables])

        variables_dict = {v: i for i, v in enumerate(variables_list)}
        x = np.array([v.value for v in variables_list])
        f = lambda x: np.hstack([e.f(variables_dict)(x) for e in component])
        df = lambda x: np.vstack([e.df(variables_dict)(x) for e in component])
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

pa = Point(0, 0, "pa")
pb = Point(10, 0, "pb")
pc = Point(10, 10, "pc")
pd = Point(20, 20, "pd")

c = [FixedX(pa, 0),
     FixedY(pa, 0),
     Horizontal(pa, pb),
     FixedDistance(pa, pb, 2),
     FixedDistance(pc, pd, 2)]

solve(c)
print(pa, pb, pc, pd)

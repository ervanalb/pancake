import numpy as np

EPSILON = 1e-10
MAX_ITER = 100

class SolverException(Exception):
    pass

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
                break
            dx = np.dot(np.linalg.pinv(df(x)), -f_x)
            x += dx
        else:
            raise SolverException("Did not converge.")

        for (xv, v) in zip(x, variables_list):
            v.value = xv

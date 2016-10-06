from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

class Feature:
    def __init__(self, parent=None):
        self.selected = False
        self.parent = parent
        self.constraints = []

    @property
    def flat_tree(self):
        return [c2 for c in self.children for c2 in c.flat_tree] + [self]

    @property
    def children(self):
        return []

    def hit(self, canvas, pos):
        return any([c.hit(canvas, pos) for c in self.children])

    def draw(self, canvas, event, qp):
        pass

    def delete_constraints(self):
        for c in self.constraints[:]:
            c.system.delete_constraint(c)
        for c in self.children:
            c.delete_constraints()

    def __str__(self):
        return "{}".format(self.__class__.__name__)

    @property
    def actions(self):
        return []

class Scalar(Feature):
    def __init__(self, val, **kwargs):
        super().__init__(**kwargs)
        self.var = Variable(val)

    def __str__(self):
        return "{}({:.3f})".format(self.__class__.__name__, self.x.value)

class Point(Feature):
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.x = Variable(x)
        self.y = Variable(y)
        self.handle_size = 10

    def __str__(self):
        return "{}({:.3f}, {:.3f})".format(self.__class__.__name__, self.x.value, self.y.value)

    def draw(self, canvas, event, qp):
        params = (canvas.xfx(self.x.value) - self.handle_size / 2, canvas.xfy(self.y.value) - self.handle_size / 2, self.handle_size, self.handle_size)
        qp.setPen(QtGui.QPen(canvas.line_color_selected if self.selected else canvas.line_color, canvas.line_width))
        qp.fillRect(*params, canvas.bg_color)
        qp.drawRect(*params)

    def hit(self, canvas, pos):
        return np.all(np.abs(pos - np.array([canvas.xfx(self.x.value), canvas.xfy(self.y.value)])) < self.handle_size / 2)

    def start_drag(self, canvas, pos):
        self.drag_start_mouse = pos
        self.drag_start_point = np.array([self.x.value, self.y.value])

    def drag(self, canvas, pos):
        new_pos = pos - self.drag_start_mouse + self.drag_start_point
        self.x.value = new_pos[0]
        self.y.value = new_pos[1]

class Line(Feature):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if len(args) == 2:
            self.p1, self.p2 = args
            self._children = []
        elif len(args) == 4:
            (x1, y1, x2, y2) = args
            self.p1 = Point(x1, y1, parent=self)
            self.p2 = Point(x2, y2, parent=self)
            self._children = [self.p1, self.p2]
        else:
            raise TypeError("Line takes 2 or 4 arguments")
        self.handle_size = 10

    @property
    def children(self):
        return self._children

    def draw(self, canvas, event, qp):
        qp.setPen(QtGui.QPen(canvas.line_color_selected if self.selected else canvas.line_color, canvas.line_width))
        qp.drawLine(canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value), canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value))
        for c in self._children:
            c.draw(canvas, event, qp)

    def hit(self, canvas, pos):
        p1 = np.array([canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value)])
        p2 = np.array([canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value)])

        dp = p2 - p1
        pv = pos - p1
        v = np.dot(pv, dp) / np.linalg.norm(dp) ** 2
        n = np.linalg.norm(pv - v * dp)

        hit = v > 0 and v < 1 and n < self.handle_size / 2
        return hit

    def start_drag(self, canvas, pos):
        self.p1.start_drag(canvas, pos)
        self.p2.start_drag(canvas, pos)

    def drag(self, canvas, pos):
        self.p1.drag(canvas, pos)
        self.p2.drag(canvas, pos)

    def delete_child(self, child):
        self.parent.delete_child(self)

class Edge(Line):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(p1, p2, **kwargs)

    @property
    def actions(self):
        return (("split", lambda:self.parent.split_edge(self)),)

class Polygon(Feature):
    def __init__(self, points, **kwargs):
        super().__init__(**kwargs)
        assert len(points) >= 2
        self.ps = [Point(p[0], p[1], parent=self) for p in points]
        self.ls = [Edge(p1, p2, parent=self) for (p1, p2) in zip(self.ps[0:-1], self.ps[1:])] + [Edge(self.ps[-1], self.ps[0], parent=self)]

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, len(self.ps))

    @property
    def children(self):
        return self.ps + self.ls

    def start_drag(self, canvas, pos):
        for p in self.ps:
            p.start_drag(canvas, pos)

    def drag(self, canvas, pos):
        for p in self.ps:
            p.drag(canvas, pos)

    def draw(self, canvas, event, qp):
        for c in self.ls + self.ps:
            c.draw(canvas, event, qp)

    def split_edge(self, edge):
        i = self.ls.index(edge)
        x = (edge.p1.x.value + edge.p2.x.value) / 2
        y = (edge.p1.y.value + edge.p2.y.value) / 2
        newp = Point(x, y, parent=self)
        l1 = Edge(self.ls[i - 1].p2, newp, parent=self)
        l2 = Edge(newp, self.ls[(i + 1) % len(self.ls)].p1, parent=self)
        self.ls[i].delete_constraints()
        del self.ls[i]
        self.ls.insert(i, l1)
        self.ls.insert(i + 1, l2)
        self.ps.insert(i + 1, newp)

    def delete_child(self, c):
        if c in self.ps:
            if len(self.ps) == 2:
                self.parent.delete_child(self)
            else:
                i = self.ps.index(c)
                self.ls[i - 1].p2 = self.ls[i].p2
                self.ps[i].delete_constraints()
                self.ls[i].delete_constraints()
                self.ls[i - 1].delete_constraints()
                del self.ps[i]
                del self.ls[i]

        elif c in self.ls:
            if len(self.ls) == 2:
                self.parent.delete_child(self)
            else:
                i = self.ls.index(c)
                self.ls[i - 1].p2 = self.ls[(i + 1) % len(self.ps)].p1
                self.ps[i].delete_constraints()
                self.ps[(i + 1) % len(self.ps)].delete_constraints()
                self.ls[i].delete_constraints()
                del self.ps[i]
                del self.ls[i]

class Scene(Feature):
    def __init__(self):
        super().__init__()
        self._children = []
        self.constraints = []

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        self._children = value

    def draw(self, canvas, event, qp):
        for c in reversed(self.children):
            c.draw(canvas, event, qp)

    def add_constraint(self, constraint):
        self.constraints.append(constraint)

    def delete_constraint(self, constraint):
        for f in constraint.features:
            f.constraints.remove(constraint)
        self.constraints.remove(constraint)

    def delete_child(self, child):
        child.delete_constraints()
        self._children.remove(child)

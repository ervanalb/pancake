from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

class Point:
    def __init__(self, x, y, name=None):
        self.x = Variable(x, "{}.x".format(name) if name is not None else None)
        self.y = Variable(y, "{}.y".format(name) if name is not None else None)
        self.name = name
        self.handle_size = 10
        self.selected = False
        self.children = []

    def __str__(self):
        if self.name is not None:
            return "{} = ({}, {})".format(self.name, self.x.value, self.y.value)
        return "({}, {})".format(self.x.value, self.y.value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self))

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

class Line:
    def __init__(self, *args, name=None):
        if len(args) == 4:
            (x1, y1, x2, y2) = args
            self.p1 = Point(x1, y1, "{}.1".format(name) if name is not None else None)
            self.p2 = Point(x2, y2, "{}.2".format(name) if name is not None else None)
            self.children = [self.p1, self.p2]
        elif len(args) == 2:
            (p1, p2) = args
            self.p1 = p1
            self.p2 = p2
            self.children = [] # assume children are already handled
        else:
            assert False
        self.name = name
        self.handle_size = 10
        self.selected = False

    def draw(self, canvas, event, qp):
        qp.setPen(QtGui.QPen(canvas.line_color_selected if self.selected else canvas.line_color, canvas.line_width))
        qp.drawLine(canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value), canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value))

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

class Polygon:
    def __init__(self, points, name=None):
        assert len(points) >= 2
        self.ps = [Point(*p) for p in points]
        self.ls = [Line(p1, p2) for (p1, p2) in zip(self.ps[0:-1], self.ps[1:])] + [Line(self.ps[-1], self.ps[0])]
        self.selected = False

    def hit(self, canvas, pos):
        return any([c.hit(canvas, pos) for c in self.children])

    def start_drag(self, canvas, pos):
        for p in self.ps:
            p.start_drag(canvas, pos)

    def drag(self, canvas, pos):
        for p in self.ps:
            p.drag(canvas, pos)

    def draw(self, canvas, event, qp):
        pass

    @property
    def children(self):
        return self.ps + self.ls

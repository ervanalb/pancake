from solver import Variable
from PyQt5 import QtWidgets
import numpy as np

class Feature:
    def mousePressEvent(self, canvas, pos):
        return False

    def mouseReleaseEvent(self, canvas, pos):
        pass

    def mouseMoveEvent(self, canvas, pos):
        pass

class Point:
    def __init__(self, x, y, name=None):
        self.x = Variable(x, "{}.x".format(name) if name is not None else None)
        self.y = Variable(y, "{}.y".format(name) if name is not None else None)
        self.name = name
        self.handle_size = 10
        self.mouse_drag = None

    def __str__(self):
        if self.name is not None:
            return "{} = ({}, {})".format(self.name, self.x.value, self.y.value)
        return "({}, {})".format(self.x.value, self.y.value)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self))

    def draw(self, canvas, event, qp):
        qp.drawRect(canvas.xfx(self.x.value) - self.handle_size / 2, canvas.xfy(self.y.value) - self.handle_size / 2, self.handle_size, self.handle_size)

    def mousePressEvent(self, canvas, pos):
        if np.all(np.abs(pos - np.array([canvas.xfx(self.x.value), canvas.xfy(self.y.value)])) < self.handle_size):
            self.mouse_drag = pos
            return True
        return False

    def mouseReleaseEvent(self, canvas, pos):
        self.mouse_drag = None

    def mouseMoveEvent(self, canvas, pos):
        if self.mouse_drag is not None:
            d = pos - self.mouse_drag
            self.mouse_drag = pos
            self.x.value += d[0] / canvas.scale
            self.y.value += d[1] / canvas.scale
            canvas.update()

class Line:
    def __init__(self, x1, y1, x2, y2, name=None):
        self.p1 = Point(x1, y1, "{}.1".format(name) if name is not None else None)
        self.p2 = Point(x2, y2, "{}.2".format(name) if name is not None else None)
        self.name = name

    def draw(self, canvas, event, qp):
        qp.drawLine(canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value), canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value))
        self.p1.draw(canvas, event, qp)
        self.p2.draw(canvas, event, qp)

    def mousePressEvent(self, canvas, pos):
        if not self.p1.mousePressEvent(canvas, pos):
            self.p2.mousePressEvent(canvas, pos)

    def mouseReleaseEvent(self, canvas, pos):
        self.p1.mouseReleaseEvent(canvas, pos)
        self.p2.mouseReleaseEvent(canvas, pos)

    def mouseMoveEvent(self, canvas, pos):
        self.p1.mouseMoveEvent(canvas, pos)
        self.p2.mouseMoveEvent(canvas, pos)

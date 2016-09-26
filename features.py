from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

def selection(selected, hit, behavior=None):
    if behavior == "set":
        return hit
    elif behavior == "add":
        return selected or hit
    elif behavior == "sub":
        return selected and not hit
    elif behavior == "toggle":
        return selected != hit
    return selected

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
        self.selected = False

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

    def hit(self, canvas, pos, behavior=None):
        hit = np.all(np.abs(pos - np.array([canvas.xfx(self.x.value), canvas.xfy(self.y.value)])) < self.handle_size / 2)
        self.selected = selection(self.selected, hit, behavior)
        return hit

    def drag(self, canvas, delta_pos):
        if self.selected:
            self.x.value += delta_pos[0]
            self.y.value += delta_pos[1]

    def deselect(self):
        self.selected = False

class Line:
    def __init__(self, x1, y1, x2, y2, name=None):
        self.p1 = Point(x1, y1, "{}.1".format(name) if name is not None else None)
        self.p2 = Point(x2, y2, "{}.2".format(name) if name is not None else None)
        self.name = name
        self.handle_size = 10
        self.selected = False

    def draw(self, canvas, event, qp):
        qp.setPen(QtGui.QPen(canvas.line_color_selected if self.selected else canvas.line_color, canvas.line_width))
        qp.drawLine(canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value), canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value))
        self.p2.draw(canvas, event, qp)
        self.p1.draw(canvas, event, qp)

    def hit(self, canvas, pos, behavior=None):
        if self.p1.hit(canvas, pos, behavior):
            return True
        if self.p2.hit(canvas, pos, behavior):
            return True

        p1 = np.array([canvas.xfx(self.p1.x.value), canvas.xfy(self.p1.y.value)])
        p2 = np.array([canvas.xfx(self.p2.x.value), canvas.xfy(self.p2.y.value)])

        dp = p2 - p1
        pv = pos - p1
        v = np.dot(pv, dp) / np.linalg.norm(dp) ** 2
        n = np.linalg.norm(pv - v * dp)

        hit = v > 0 and v < 1 and n < self.handle_size / 2
        self.selected = selection(self.selected, hit, behavior)
        return hit

    def drag(self, canvas, delta_pos):
        if self.selected:
            self.p1.x.value += delta_pos[0]
            self.p1.y.value += delta_pos[1]
            self.p2.x.value += delta_pos[0]
            self.p2.y.value += delta_pos[1]
        else:
            self.p1.drag(canvas, delta_pos)
            self.p2.drag(canvas, delta_pos)

    def deselect(self):
        self.selected = False
        self.p1.deselect()
        self.p2.deselect()


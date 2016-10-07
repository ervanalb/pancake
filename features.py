from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

class Feature:
    def __init__(self, scene=None):
        self.selected = False
        self.scene = scene
        self.constraints = []
        self.dependents = []
        self.dependees = []

    def draw(self, canvas, event, qp, **kwargs):
        pass

    def delete(self):
        for c in self.constraints[:]:
            if c in self.constraints:
                c.delete()
        for d in self.dependents[:]:
            if d in self.dependents:
                d.delete()
        for d in self.dependees[:]:
            if d in self.dependees:
                d.dependents.remove(self)

        if self.scene is not None and self in self.scene.features:
            self.scene.features.remove(self)

        # Do not use this object after this point
        self.scene = None
        self.constraints = []
        self.dependents = []
        self.dependees = []

    def depends_on(self, dependees):
        self.dependees += list(dependees)
        for dependee in dependees:
            dependee.dependents.append(self)

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

    def draw(self, canvas, event, qp, **kwargs):
        selected = kwargs.get("selected", self.selected)
        params = (canvas.xfx(self.x.value) - self.handle_size / 2, canvas.xfy(self.y.value) - self.handle_size / 2, self.handle_size, self.handle_size)
        qp.setPen(QtGui.QPen(canvas.line_color_selected if selected else canvas.line_color, canvas.line_width))
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
    def __init__(self, p1, p2, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2
        self.depends_on((p1, p2))
        self.handle_size = 10

    def draw(self, canvas, event, qp, **kwargs):
        selected = kwargs.get("selected", self.selected)

        qp.setPen(QtGui.QPen(canvas.line_color_selected if selected else canvas.line_color, canvas.line_width))
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

from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np
import features

class FeatureCreator:
    def __init__(self, canvas):
        canvas.mode = "create"
        canvas.create = self
        self.init(canvas)

    def init(self):
        pass

    def mousePressEvent(self, canvas, pos):
        pass

    def mouseMoveEvent(self, canvas, pos):
        pass

    def mouseReleaseEvent(self, canvas, pos):
        pass

    def keyPressEvent(self, canvas, key):
        if key == Qt.Key_Escape:
            self.over(canvas)

    def over(self, canvas):
        canvas.mode = "select"
        canvas.create = None
        canvas.update()

    def draw(self, canvas, event, qp):
        pass

class PointCreator(FeatureCreator):
    def init(self, canvas):
        self.point = features.Point(0, 0)

    def mousePressEvent(self, canvas, pos):
        canvas.scene.add_feature(self.point)
        self.point = features.Point(0, 0)
        canvas.update()

    def mouseMoveEvent(self, canvas, pos):
        (self.point.x.value, self.point.y.value) = tuple(pos)
        canvas.update()

    def draw(self, canvas, event, qp):
        self.point.draw(canvas, event, qp)

class LineCreator(FeatureCreator):
    def init(self, canvas):
        self.pt1 = None
        self.mouse = None

    def mousePressEvent(self, canvas, pos):
        if self.pt1 is None:
            f = canvas.hit(pos)
            if f is not None and isinstance(f, features.Point):
                self.pt1 = f
                self.pt1_new = False
            else:
                self.pt1 = features.Point(*tuple(pos))
                self.pt1_new = True
            self.mouse = pos
            canvas.update()
        else:
            f = canvas.hit(pos)
            if f is not None and isinstance(f, features.Point):
                pt2 = f
            else:
                pt2 = features.Point(*tuple(pos))
                canvas.scene.add_feature(pt2)
            line = features.Line(self.pt1, pt2)
            line.depends_on((self.pt1, pt2))
            if self.pt1_new:
                canvas.scene.add_feature(self.pt1)
            canvas.scene.add_feature(line)
            self.pt1 = None
            canvas.update()

    def mouseMoveEvent(self, canvas, pos):
        if self.mouse is not None:
            self.mouse = pos
            canvas.update()

    def draw(self, canvas, event, qp):
        if self.pt1 is not None:
            qp.setPen(QtGui.QPen(canvas.line_color, canvas.line_width))
            qp.drawLine(canvas.xfx(self.pt1.x.value), canvas.xfy(self.pt1.y.value), canvas.xfx(self.mouse[0]), canvas.xfy(self.mouse[1]))
            self.pt1.draw(canvas, event, qp)

available = (
    PointCreator,
    LineCreator
)

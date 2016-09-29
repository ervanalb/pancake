import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import features
import constraints
import solver
import numpy as np

def flatten_feature_tree(features):
    return [f2 for f in features for f2 in flatten_feature_tree(f.children) + [f]]

class Canvas(QtWidgets.QWidget):
    STANDARD_DPI = 96
    SCROLL_FACTOR = 1.01

    def __init__(self):
        super().__init__()
        self.initUI()
        self.features = []
        self.constraints = []
        self.dpi_scale = QtWidgets.QApplication.screens()[0].logicalDotsPerInch() / self.STANDARD_DPI
        self.scale = 1.
        self.translate = np.array([0., 0.])
        self.drag_view = None
        self.drag_features = None

        self.bg_color = Qt.white
        self.line_color = Qt.blue
        self.line_color_selected = Qt.green
        self.line_width = 2

    def initUI(self):
        pass

    def xfx(self, x):
        return (x + self.translate[0]) * self.scale

    def xfy(self, y):
        return (y + self.translate[1]) * self.scale

    def ixfx(self, x):
        return x / self.scale - self.translate[0]

    def ixfy(self, y):
        return y / self.scale - self.translate[1]

    def recalculate(self):
        solver.solve(self.constraints)

    def paintEvent(self, event):
        self.recalculate()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.scale(self.dpi_scale, self.dpi_scale)
        for f in reversed(flatten_feature_tree(self.features)):
            f.draw(self, event, qp)
        qp.end()

    def wheelEvent(self, event):
        factor = self.SCROLL_FACTOR ** event.angleDelta().y()
        self.scale *= factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = np.array([event.x(), event.y()]) / self.dpi_scale
            self.drag_features = np.array([self.ixfx(pos[0]), self.ixfy(pos[1])])
            for f in flatten_feature_tree(self.features):
                f.selected = False

            for f in flatten_feature_tree(self.features):
                if f.hit(self, pos):
                    f.selected = True
                    f.start_drag(self, self.drag_features)
                    break

            self.update()
        elif event.button() == Qt.RightButton:
            self.drag_view = np.array([event.x(), event.y()])

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_features = None
        elif event.button() == Qt.RightButton:
            self.drag_view = None

    def mouseMoveEvent(self, event):
        if self.drag_features is not None:
            pos = np.array([event.x(), event.y()]) / self.dpi_scale
            pos = np.array([self.ixfx(pos[0]), self.ixfy(pos[1])])

            for f in flatten_feature_tree(self.features):
                if f.selected:
                    f.drag(self, pos)
            self.update()

        if self.drag_view is not None:
            pos = np.array([event.x(), event.y()])
            d = (pos - self.drag_view) / self.dpi_scale
            self.translate += d / self.scale
            self.drag_view = pos
            self.update()

def main():
    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QWidget()
    w.setWindowTitle("Pancake")

    c = Canvas()

    vbox = QtWidgets.QVBoxLayout()
    vbox.addWidget(c)
    w.setLayout(vbox)
    w.show()

    c.features = [
        features.Polygon([(0, 0), (10, 0), (10, 10)])
    ]

    c.constraints = [
        constraints.FixedDistance(c.features[0].ps[0], c.features[0].ps[1], 10),
        constraints.FixedDistance(c.features[0].ps[1], c.features[0].ps[2], 10),
        constraints.FixedDistance(c.features[0].ps[2], c.features[0].ps[0], 10)
    ]

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

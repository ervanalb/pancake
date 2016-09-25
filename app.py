import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import features
import constraints
import solver
import numpy as np

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

    def initUI(self):
        pass

    def xfx(self, x):
        return (x + self.translate[0]) * self.scale

    def xfy(self, y):
        return (y + self.translate[1]) * self.scale

    def recalculate(self):
        solver.solve(self.constraints)

    def paintEvent(self, event):
        self.recalculate()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.scale(self.dpi_scale, self.dpi_scale)
        for f in self.features:
            f.draw(self, event, qp)
        qp.end()

    def wheelEvent(self, event):
        factor = self.SCROLL_FACTOR ** event.angleDelta().y()
        self.scale *= factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = np.array([event.x(), event.y()]) / self.dpi_scale
            for f in self.features:
                if f.mousePressEvent(self, pos):
                    break
        elif event.button() == Qt.RightButton:
            self.drag_view = np.array([event.x(), event.y()])

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = np.array([event.x(), event.y()]) / self.dpi_scale
            for f in self.features:
                f.mouseReleaseEvent(self, pos)
        elif event.button() == Qt.RightButton:
            self.drag_view = None

    def mouseMoveEvent(self, event):
        pos = np.array([event.x(), event.y()]) / self.dpi_scale
        for f in self.features:
            f.mouseMoveEvent(self, pos)

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
        features.Line(0, 0, 0, 10),
        features.Line(0, 0, 5, 10),
        features.Line(0, 10, 5, 10)
    ]

    d = solver.Variable(1, "d")

    c.constraints = [
        constraints.FixedX(c.features[0].p1, 0),
        constraints.FixedY(c.features[0].p1, 0),
        constraints.Equal(c.features[0].p1.x, c.features[1].p1.x),
        constraints.Equal(c.features[0].p1.y, c.features[1].p1.y),
        constraints.Equal(c.features[0].p2.x, c.features[2].p1.x),
        constraints.Equal(c.features[0].p2.y, c.features[2].p1.y),
        constraints.Equal(c.features[1].p2.x, c.features[2].p2.x),
        constraints.Equal(c.features[1].p2.y, c.features[2].p2.y),
        constraints.Distance(c.features[0].p1, c.features[0].p2, d),
        constraints.Distance(c.features[1].p1, c.features[1].p2, d),
        constraints.Distance(c.features[2].p1, c.features[2].p2, d),
        #constraints.FixedY(c.features[0].p2, 0),
    ]

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

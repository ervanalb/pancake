import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import features
import featurecreator
import constraints
import solver
import numpy as np

class Canvas(QtWidgets.QWidget):
    STANDARD_DPI = 96
    SCROLL_FACTOR = 1.001

    def __init__(self, scene, update_fn):
        self.scene = scene
        self.update_fn = update_fn
        super().__init__()
        self.initUI()
        self.dpi_scale = QtWidgets.QApplication.screens()[0].logicalDotsPerInch() / self.STANDARD_DPI
        self.scale = 1.
        self.translate = np.array([0., 0.])
        self.drag_view = None
        self.drag_features = None

        self.mode = "select"

        self.bg_color = Qt.white
        self.line_color = Qt.blue
        self.line_color_selected = Qt.green
        self.line_width = 2

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

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
        try:
            solver.solve(self.scene.constraints)
            self.line_color = Qt.blue
        except solver.SolverException:
            self.line_color = Qt.red

    def paintEvent(self, event):
        self.recalculate()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.scale(self.dpi_scale, self.dpi_scale)
        self.scene.draw(self, event, qp)
        if self.mode == "create":
            self.create.draw(self, event, qp)
        qp.end()

    def wheelEvent(self, event):
        factor = self.SCROLL_FACTOR ** event.angleDelta().y()
        self.scale *= factor
        self.update_fn()

    def keyPressEvent(self, event):
        if self.mode == "create":
            self.create.keyPressEvent(self, event.key())

        elif self.mode == "select":
            if event.key() == Qt.Key_Delete:
                to_delete = list(self.scene.flat_tree)
                for f in to_delete:
                    if f in self.scene.flat_tree and f.selected:
                        f.parent.delete_child(f)
                self.update_fn()

    def mousePressEvent(self, event):
        pos = np.array([event.x(), event.y()]) / self.dpi_scale
        scene_pos = np.array([self.ixfx(pos[0]), self.ixfy(pos[1])])

        if event.button() == Qt.LeftButton:
            if self.mode == "select":
                self.drag_features = scene_pos

                features = self.scene.flat_tree
                if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
                    for f in features:
                        if f.hit(self, pos):
                            f.selected = True
                            break
                elif QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier:
                    for f in features:
                        if f.hit(self, pos):
                            f.selected = not f.selected
                            break
                else: 

                    for f in features:
                        if f.hit(self, pos):
                            if not f.selected:
                                for f2 in features:
                                    f2.selected = False
                            f.selected = True
                            break
                    else:
                        for f2 in features:
                            f2.selected = False

                for f in features:
                    if f.selected:
                        f.start_drag(self, scene_pos)
                self.update_fn()
            elif self.mode == "create":
                self.create.mousePressEvent(self, scene_pos)

        elif event.button() == Qt.MiddleButton:
            self.drag_view = pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = np.array([event.x(), event.y()]) / self.dpi_scale
            scene_pos = np.array([self.ixfx(pos[0]), self.ixfy(pos[1])])
            if self.mode == "select":
                self.drag_features = None
            elif self.mode == "create":
                self.create.mouseReleaseEvent(self, scene_pos)
        elif event.button() == Qt.MiddleButton:
            self.drag_view = None

    def mouseMoveEvent(self, event):
        pos = np.array([event.x(), event.y()]) / self.dpi_scale
        scene_pos = np.array([self.ixfx(pos[0]), self.ixfy(pos[1])])

        if self.mode == "create":
            self.create.mouseMoveEvent(self, scene_pos)

        elif self.drag_features is not None:
            for f in self.scene.flat_tree:
                if f.selected:
                    f.drag(self, scene_pos)
            self.update_fn()

        elif self.drag_view is not None:
            d = (pos - self.drag_view)
            self.translate += d / self.scale
            self.drag_view = pos
            self.update_fn()

    def contextMenuEvent(self, event):
        selected = [f for f in self.scene.flat_tree if f.selected]
        if len(selected) >= 1:
            menu = QtWidgets.QMenu(self)

            # Actions
            available_actions = [(action_name, [action_function] + [dict(feature.actions)[action_name] for feature in selected[1:]])
                                 for (action_name, action_function) in selected[0].actions
                                 if all([action_name in dict(feature.actions) for feature in selected[1:]])]
            action_menu_items = [(menu.addAction(action_name), action_functions) for (action_name, action_functions) in available_actions]

            # Constraints
            available_constraints = [constraint_class for constraint_class in constraints.available if constraint_class.compatible(selected)]
            constraint_menu_items = [(menu.addAction(constraint_class.__name__), constraint_class) for constraint_class in available_constraints]

            result = menu.exec_(self.mapToGlobal(event.pos()))
            for (menu_action, action_functions) in action_menu_items:
                if result == menu_action:
                    for af in action_functions:
                        af()
                    break
            else:
                for (menu_constraint, constraint_class) in constraint_menu_items:
                    if result == menu_constraint:
                        self.scene.add_constraint(constraint_class(*selected, system=self.scene))
                        break

            self.update_fn()

class FeatureTree(QtWidgets.QTreeWidget):
    def __init__(self, scene, update_fn):
        self.scene = scene
        self.update_fn = update_fn
        super().__init__()
        self.initUI()
        self.itemExpanded.connect(self.onItemExpanded)
        self.itemCollapsed.connect(self.onItemCollapsed)
        self.itemSelectionChanged.connect(self.onItemSelectionChanged)
        self.updating = False

    def onItemExpanded(self, qtwi):
        qtwi.feature.q_expanded = True

    def onItemCollapsed(self, qtwi):
        qtwi.feature.q_expanded = False

    def onItemSelectionChanged(self):
        if self.updating:
            return
        def crawl(item):
            item.feature.selected = item.isSelected()
            for i in range(item.childCount()):
                crawl(item.child(i))

        for i in range(self.topLevelItemCount()):
            crawl(self.topLevelItem(i))
        self.update_fn()

    def initUI(self):
        self.header().close()
        #self.setStyleSheet("QTreeWidget {border: none; background: transparent;}")

    def update(self):
        self.updating = True
        to_expand = []
        to_select = []
        def treeify(f):
            if not hasattr(f, "q_expanded"):
                f.q_expanded = False
            item = QtWidgets.QTreeWidgetItem([str(f)])
            if f.q_expanded:
                to_expand.append(item)
            if f.selected:
                to_select.append(item)
            item.feature = f
            for sub_f in f.children:
                item.addChild(treeify(sub_f))
            return item

        self.clear()
        self.addTopLevelItems(treeify(self.scene).takeChildren())
        for item in to_expand:
            item.setExpanded(True)
        for item in to_select:
            item.setSelected(True)
        super().update()
        self.updating = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            to_delete = list(self.scene.flat_tree)
            for f in to_delete:
                if f in self.scene.flat_tree and f.selected:
                    self.scene.delete(f)
            self.update_fn()

def add_menus(mb):
    create_menu = mb.addMenu("&Create")
    for fc in featurecreator.available:
        action = QtWidgets.QAction(fc.__name__, create_menu)
        def wrap(fc_):
            return lambda:fc_(canvas)
        action.triggered.connect(wrap(fc))
        create_menu.addAction(action)

def main():
    global scene
    global canvas

    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QMainWindow()
    w.setWindowTitle("Pancake")

    def update_fn():
        canvas.update()
        feature_tree.update()

    scene = features.Scene()
    canvas = Canvas(scene, update_fn)
    feature_tree = FeatureTree(scene, update_fn)

    splitter = QtWidgets.QSplitter()

    splitter.addWidget(feature_tree)
    splitter.addWidget(canvas)

    w.setCentralWidget(splitter)

    add_menus(w.menuBar())

    w.show()

    scene.children = [
        features.Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], parent=scene)
    ]

    scene.constraints = [
        constraints.FixedDistance(scene.children[0].ps[0], scene.children[0].ps[1], 10, system=scene),
        constraints.FixedX(scene.children[0].ps[0], 0, system=scene),
        constraints.FixedY(scene.children[0].ps[0], 0, system=scene),
        #constraints.Vertical(scene.children[0].ps[0], scene.children[0].ps[1], system=scene),
        #constraints.Horizontal(scene.children[0].ps[1], scene.children[0].ps[2], system=scene),
        #constraints.Vertical(scene.children[0].ps[2], scene.children[0].ps[3], system=scene),
        #constraints.Horizontal(scene.children[0].ps[3], scene.children[0].ps[0], system=scene)
    ]

    update_fn()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

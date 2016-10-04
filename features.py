from solver import Variable
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

class Feature:
    def __init__(self):
        self.selected = False

    @property
    def flat_tree(self):
        return [c2 for c in self.children for c2 in c.flat_tree] + [self]

    @property
    def children(self):
        return []

    def hit(self, canvas, pos):
        return any([c.hit(canvas, pos) for c in self.children])

    def delete_child(self, c):
        """ This method should delete child c from this feature's children. It should
        return as a set any additional children that were deleted. If deletion of the given
        child should cause this feature to be deleted entirely, self is returned.
        """

        return set()

    def __str__(self):
        return "{}".format(self.__class__.__name__)

class Point(Feature):
    def __init__(self, x, y):
        super().__init__()
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
    def __init__(self, *args):
        super().__init__()
        if len(args) == 4:
            (x1, y1, x2, y2) = args
            self.p1 = Point(x1, y1)
            self.p2 = Point(x2, y2)
            self._children = [self.p1, self.p2]
        elif len(args) == 2:
            (p1, p2) = args
            self.p1 = p1
            self.p2 = p2
            self._children = [] # assume children are already handled
        else:
            assert False
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

    def delete_child(self, c):
        return self

class Polygon(Feature):
    def __init__(self, points, name=None):
        super().__init__()
        assert len(points) >= 2
        self.ps = [Point(*p) for p in points]
        self.ls = [Line(p1, p2) for (p1, p2) in zip(self.ps[0:-1], self.ps[1:])] + [Line(self.ps[-1], self.ps[0])]

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

    def delete_child(self, c):
        if c in self.ps:
            if len(self.ps) == 2:
                return self
            else:
                i = self.ps.index(c)
                self.ls[i - 1].p2 = self.ls[i].p2
                ret = {self.ls[i], self.ls[i - 1]}
                del self.ps[i]
                del self.ls[i]
                return ret

        elif c in self.ls:
            if len(self.ls) == 2:
                return self
            else:
                i = self.ls.index(c)
                self.ls[i - 1].p2 = self.ls[(i + 1) % len(self.ps)].p1
                ret = {self.ps[i], self.ps[(i + 1) % len(self.ps)]}
                del self.ps[i]
                del self.ls[i]
                return ret

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

    def delete_child(self, feature):
        self._children.remove(feature)
        return set()

    def delete(self, feature_to_delete):
        def descend_and_delete(parent):
            # Returns False if feature was deleted and parent doesn't need to be deleted
            # Returns True if feature was deleted and parent does need to be deleted
            # Returns None if feature was not deleted (not found in tree)
            if feature_to_delete in parent.children:
                deleted = parent.delete_child(feature_to_delete)
                if deleted == parent:
                    return True
                else:
                    self.delete_constraints_containing(deleted | set(feature_to_delete.flat_tree))
                    return False
            else:
                for c in parent.children:
                    result = descend_and_delete(c)
                    if result is False:
                        return False
                    elif result is True:
                        deleted = parent.delete_child(c)
                        if deleted == parent:
                            return True
                        else:
                            self.delete_constraints_containing(deleted | set(c.flat_tree))
                            return False
        result = descend_and_delete(self)
        assert result is False

    def delete_constraints_containing(self, features):
        to_delete = {c for f in features for c in self.constraints if f in c.features}
        self.constraints = [c for c in self.constraints if c not in to_delete]           

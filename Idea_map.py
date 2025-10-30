from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsLineItem, QGraphicsView
from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import QPen, QColor


class Idea(QGraphicsItem):
    '''Класс идеи'''

    def __init__(self, text: str, scene, treeRow: int, parentIdea=None):
        super().__init__()
        self.text = text
        self.ideaMapScene = scene
        self.parentIdea = parentIdea
        self.childs = []
        self.treeRow = treeRow

    def boundingRect(self) -> QtCore.QRectF:
        '''Переопределенный метод определения размеров ограничивающего прямоугольника'''
        font_metrics = QtGui.QFontMetrics(QtGui.QFont(
        ))  # QFont - класс информации о шрифте, QFontMetrics - информация о высоте, ширине символа, общей ширине текста
        # horizontalAdvance - информация следующему символу текста, где быть размещенным, в зависимости от ширины предыдущего символа
        text_width = font_metrics.horizontalAdvance(self.text) + 20
        text_height = font_metrics.height() + 10
        return QtCore.QRectF(0, 0, text_width, text_height)

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget) -> None:
        '''Переопределенный метод отрисовки класса Idea'''
        rect = self.boundingRect()  # рисуем в пределах этого прямоугольника
        painter.drawRect(rect)
        painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.text)

    def addChild(self, child) -> bool:
        '''Метод добавления дочерней мысли'''
        if isinstance(child, Idea):
            self.childs.append(child)
            child.parentIdea = self
            return True
        else:
            return False


class IdeaMap(QGraphicsScene):
    '''Класс карты мыслей'''

    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        super().__init__(self.projectWindow)
        # self.treeView = projectWindow.treeView
        self.setViewportSizeToScene()
        self.rootIdea = Idea("Первая мысль", self, 0)
        self.addItem(self.rootIdea)
        self.setIdeaPos(self.rootIdea)

    # Этот метод нужен для того, чтобы правильно рассчитывать высоту, 
    # отведенную каждой дочерней идее, т.к. лэйаут меняет реальные размеры сцены
    def setViewportSizeToScene(self):
        '''Метод для получения размера viewport после его изменения лэйаутом'''
        viewport = self.projectWindow.treeView.viewport()
        vp_size = viewport.size()
        self.setSceneRect(0, 0, vp_size.width(), vp_size.height())

    def connectIdeas(self, parentIdea: Idea, childIdea: Idea) -> bool:
        '''Метод для соединения двух идей линией'''
        if childIdea in parentIdea.childs:
            parentRect = parentIdea.boundingRect()
            childRect = childIdea.boundingRect()
            point1 = QPointF(parentIdea.pos().x() + parentRect.width(),
                             parentIdea.pos().y() + parentRect.height() / 2)
            point2 = QPointF(childIdea.pos().x(),
                             childIdea.pos().y() + childRect.height() / 2)

            line = QGraphicsLineItem(QLineF(point1, point2))
            pen = QPen(QColor(255, 255, 255))
            pen.setWidth(1)
            line.setPen(pen)
            self.addItem(line)
            return True
        else:
            return False

    def addIdea(self, text: str, parentIdea: Idea) -> None:
        '''Метод добавления идеи в карту мыслей'''
        childIdea = Idea(text, self, parentIdea.treeRow + 1, parentIdea)
        parentIdea.addChild(childIdea)
        self.addItem(childIdea)
        self.setIdeaPos(childIdea)
        self.connectIdeas(parentIdea, childIdea)

    def getAllocatedIdeaHeight(self, idea: Idea):
        '''Метод для получения высоты, отведенной одной идее'''
        if not idea.parentIdea:  # если идея корневая
            return self.height()

        parentHeight = self.getAllocatedIdeaHeight(idea.parentIdea)
        return parentHeight / len(idea.parentIdea.childs)

    def setIdeaPos(self, idea: Idea):
        '''Метод для позиционирования идеи на сцене'''
        scene_height = self.height()

        if idea.parentIdea:  # если идея не корневая
            childIndex = idea.parentIdea.childs.index(idea)

            x = idea.parentIdea.pos().x() + idea.parentIdea.boundingRect().width() + 20

            if childIndex != 0:  # если ребенок не первый
                if idea.parentIdea.parentIdea:
                    parentHeight = self.getAllocatedIdeaHeight(idea.parentIdea)
                    parentY = idea.parentIdea.pos().y()
                else:
                    parentHeight = scene_height
                    parentY = 0

                y = parentY + (childIndex * (parentHeight /
                               len(idea.parentIdea.childs)))
            else:
                y = idea.parentIdea.pos().y()
        else:  # если корневая
            x = 0
            y = scene_height / 2

        idea.setPos(x, y)
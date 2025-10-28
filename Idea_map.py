from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsLineItem, QGraphicsView
from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import QPen, QColor


class Idea(QGraphicsItem):
    '''Класс идеи'''

    def __init__(self, text: str, scene, parentIdea=None):
        super().__init__()
        self.text = text
        self.ideaMapScene = scene
        self.parentIdea = parentIdea
        self.childs = []

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
        self.rootIdea = Idea("Первая мысль", self)
        self.addItem(self.rootIdea)
        self.setIdeaPos(self.rootIdea)

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
        childIdea = Idea(text, self, parentIdea)
        parentIdea.addChild(childIdea)
        self.addItem(childIdea)
        self.setIdeaPos(childIdea)
        self.connectIdeas(parentIdea, childIdea)

    def setIdeaPos(self, idea: Idea):
        '''Метод для позиционирования идеи на сцене'''
        if idea.parentIdea:  # если идея не корневая
            # если эта идея не первый ребенок
            if idea.parentIdea.childs[0] != idea:
                ideaIndex = idea.parentIdea.childs.index(idea)
                x = idea.parentIdea.childs[ideaIndex - 1].pos().x()
                y = idea.parentIdea.childs[ideaIndex - 1].pos().y(
                ) + idea.parentIdea.childs[ideaIndex - 1].boundingRect().height() + 20
            else:
                x = idea.parentIdea.pos().x() + idea.parentIdea.boundingRect().width() + 20
                y = idea.parentIdea.pos().y()
        else:  # если корневая
            x = -180
            y = idea.boundingRect().height()

        idea.setPos(x, y)

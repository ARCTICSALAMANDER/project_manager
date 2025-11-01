from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsLineItem, QGraphicsView, QPushButton, QGraphicsProxyWidget, QLineEdit
from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import QPen, QColor


class Line(QGraphicsLineItem):
    def __init__(self, line: QLineF, parentIdea, childIdea):
        super().__init__(line)
        self.parentIdea = parentIdea
        self.childIdea = childIdea


class Idea(QGraphicsItem):
    '''Класс идеи'''

    def __init__(self, text: str, scene, treeRow: int, parentIdea=None):
        super().__init__()
        self.ideaMapScene = scene
        self.parentIdea = parentIdea
        self.childs = []
        self.treeRow = treeRow
        
        self.textEditProxy = QGraphicsProxyWidget(self)
        self.textEdit = QLineEdit(text)
        self.textEdit.setStyleSheet('''
            background-color: black;
            color: white;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.textEditProxy.setWidget(self.textEdit)        
        # сигнал изменения текста для обновления размера
        self.textEdit.textChanged.connect(self.updateSize)
        
        self.addButtonProxy = QGraphicsProxyWidget(self)
        self.deleteButtonProxy = QGraphicsProxyWidget(self)
        
        self.addButton = QPushButton("+")
        self.addButton.setFixedSize(20, 20)
        self.addButton.setStyleSheet('''
            background-color: white;
            color: black;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.addButtonProxy.setWidget(self.addButton)
        
        self.deleteButton = QPushButton("×")
        self.deleteButton = QPushButton("×")
        self.deleteButton.setFixedSize(20, 20)
        self.deleteButton.setStyleSheet('''
            background-color: #c82333;
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.deleteButtonProxy.setWidget(self.deleteButton)    

        self.parentLine: Line | None = None
        self.childLines = []

        self.textEdit.textChanged.connect(self.updateAllLinesPos)
        
    def updateSize(self):
        '''Обновляем размер при изменении текста'''
        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QtCore.QRectF:
        '''Переопределенный метод определения размеров ограничивающего прямоугольника'''
        font_metrics = QtGui.QFontMetrics(QtGui.QFont())
        
        # Используем текущий текст из QLineEdit для расчета ширины
        current_text = self.textEdit.text()
        text_width = font_metrics.horizontalAdvance(current_text) + 40  # +20px padding с каждой стороны
        if text_width < 100:  # минимальная ширина
            text_width = 100
            
        text_height = font_metrics.height() + 20  # +10px padding сверху и снизу
        
        total_height = text_height + 30  # 30px дополнительно для кнопок
        
        return QtCore.QRectF(0, 0, text_width, total_height)

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget) -> None:
        '''Переопределенный метод отрисовки класса Idea'''
        rect = self.boundingRect()
        
        # основной прямоугольник только для текстовой части
        text_rect = QtCore.QRectF(0, 0, rect.width(), rect.height() - 30)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(text_rect)
        
        self.textEditProxy.setPos(0, 0)
        self.textEdit.setFixedSize(int(text_rect.width()), int(text_rect.height()))

        # Ставим кнопки
        button_y = rect.height() - 35
        self.addButtonProxy.setPos(rect.width() / 2 - 25, button_y) # числа 25 и 5 в формуле подогнаны по пикселям
        self.deleteButtonProxy.setPos(rect.width() / 2 + 5, button_y)

    def updateAllLinesPos(self):
        '''Метод для обновления позиций всех линий, соединенных с этой идеей'''
        if self.parentLine: # если вдруг изменили текст корневой идеи
            self.updateLinePos(self.parentLine)
        
        for i in range(len(self.childLines)):
            self.updateLinePos(self.childLines[i])

    def updateLinePos(self, line: Line):
        '''метод для повторной отрисовки линий между идеями после изменений текста в них'''
        parentRect = line.parentIdea.boundingRect()
        childRect = line.childIdea.boundingRect()
        point1 = QPointF(line.parentIdea.pos().x() + parentRect.width(), line.parentIdea.pos().y() + parentRect.height() - 50)
        point2 = QPointF(line.childIdea.pos().x(), line.childIdea.pos().y() + childRect.height() / 2 - 15)
        new_line = QLineF(point1, point2)
        line.setLine(new_line)

    def addChild(self, child) -> bool:
        '''Метод добавления дочерней мысли'''
        if isinstance(child, Idea):
            self.childs.append(child)
            child.parentIdea = self
            return True
        else:
            return False

    def getText(self) -> str:
        '''Получение текста идеи'''
        return self.textEdit.text()

    def setText(self, text: str):
        '''Установка текста идеи'''
        self.textEdit.setText(text)


class IdeaMap(QGraphicsScene):
    '''Класс карты мыслей'''

    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        super().__init__(self.projectWindow)
        self.setViewportSizeToScene()
        self.rootIdea = Idea("Первая мысль", self, 0)
        self.addItem(self.rootIdea)
        self.setIdeaPos(self.rootIdea)
        self.lines = [] # список линий между идеями

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
                             parentIdea.pos().y() + parentRect.height() - 50)
            point2 = QPointF(childIdea.pos().x(),
                             childIdea.pos().y() + childRect.height() / 2 - 15)

            line = Line(QLineF(point1, point2), parentIdea, childIdea)
            pen = QPen(QColor(255, 255, 255))
            pen.setWidth(1)
            line.setPen(pen)
            self.addItem(line)
            
            parentIdea.childLines.append(line)
            childIdea.parentLine = line

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
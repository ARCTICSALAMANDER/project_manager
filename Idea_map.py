from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsLineItem, QGraphicsView, QPushButton, QGraphicsProxyWidget, QLineEdit
from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import QPen, QColor


class Line(QGraphicsLineItem):
    def __init__(self, line: QLineF, parent_idea, child_idea):
        super().__init__(line)
        self.parent_idea = parent_idea
        self.child_idea = child_idea


class Idea(QGraphicsItem):
    '''Класс идеи'''

    def __init__(self, scene, tree_row: int, text: str = "", parent_idea=None):
        super().__init__()
        self.idea_map_scene = scene
        self.parent_idea = parent_idea
        self.childs = []
        self.tree_row = tree_row

        self.is_dragging = False
        self.old_pos = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.text_edit_proxy = QGraphicsProxyWidget(self)
        self.text_edit = QLineEdit(text)
        self.text_edit.setStyleSheet('''
            background-color: black;
            color: white;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.text_edit_proxy.setWidget(self.text_edit)
        # сигнал изменения текста для обновления размера
        self.text_edit.textChanged.connect(self.update_size)

        self.add_button_proxy = QGraphicsProxyWidget(self)
        self.delete_button_proxy = QGraphicsProxyWidget(self)

        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(20, 20)
        self.add_button.setStyleSheet('''
            background-color: white;
            color: black;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.add_button.clicked.connect(
            lambda: self.idea_map_scene.add_idea("", self))
        self.add_button_proxy.setWidget(self.add_button)

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.setStyleSheet('''
            background-color: #c82333;
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
        ''')
        self.delete_button.pressed.connect(
            lambda: self.idea_map_scene.delete_idea(self))
        self.delete_button_proxy.setWidget(self.delete_button)

        self.parent_line: Line | None = None
        self.child_lines = []

        self.text_edit.textChanged.connect(self.update_all_lines_pos)

    def update_size(self):
        '''Обновляем размер при изменении текста'''
        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QtCore.QRectF:
        '''Переопределенный метод определения размеров ограничивающего прямоугольника'''
        font_metrics = QtGui.QFontMetrics(QtGui.QFont())

        # Используем текущий текст из QLineEdit для расчета ширины
        current_text = self.text_edit.text()
        text_width = font_metrics.horizontalAdvance(
            current_text) + 40  # +20px padding с каждой стороны
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

        self.text_edit_proxy.setPos(0, 0)
        self.text_edit.setFixedSize(
            int(text_rect.width()), int(text_rect.height()))

        # Ставим кнопки
        button_y = rect.height() - 35
        # числа 25 и 5 в формуле подогнаны по пикселям
        self.add_button_proxy.setPos(rect.width() / 2 - 25, button_y)
        self.delete_button_proxy.setPos(rect.width() / 2 + 5, button_y)

    def shape(self) -> QtGui.QPainterPath:
        '''Определитель точной области для клика и перетаскивания'''
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def itemChange(self, change, value):
        """Обрабатываем изменения позиции и обновляем линии"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.update_all_lines_pos()

        return super().itemChange(change, value)

    def update_all_lines_pos(self):
        '''Метод для обновления позиций всех линий, соединенных с этой идеей'''
        if self.parent_line:  # если вдруг изменили текст корневой идеи
            self.update_line_pos(self.parent_line)

        for i in range(len(self.child_lines)):
            self.update_line_pos(self.child_lines[i])

    def update_line_pos(self, line: Line):
        '''метод для повторной отрисовки линий между идеями после изменений текста в них'''
        parent_rect = line.parent_idea.boundingRect()
        child_rect = line.child_idea.boundingRect()
        point1 = QPointF(line.parent_idea.pos().x() + parent_rect.width(),
                         line.parent_idea.pos().y() + parent_rect.height() - 50)
        point2 = QPointF(line.child_idea.pos().x(),
                         line.child_idea.pos().y() + child_rect.height() / 2 - 15)
        new_line = QLineF(point1, point2)
        line.setLine(new_line)

    def add_child(self, child) -> bool:
        '''Метод добавления дочерней мысли'''
        if isinstance(child, Idea):
            self.childs.append(child)
            child.parent_idea = self
            return True
        else:
            return False

    def get_text(self) -> str:
        '''Получение текста идеи'''
        return self.text_edit.text()

    def set_text(self, text: str):
        '''Установка текста идеи'''
        self.text_edit.setText(text)


class IdeaMap(QGraphicsScene):
    '''Класс карты мыслей'''

    def __init__(self, project_window):
        self.project_window = project_window
        super().__init__(self.project_window)
        self.set_viewport_size_to_scene()
        self.root_idea = Idea(self, 0, text="Первая мысль")
        self.addItem(self.root_idea)
        self.set_idea_pos(self.root_idea)
        self.lines = []  # список линий между идеями

        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

    def update_all_lines_for_idea(self, idea: Idea):
        '''Обновляем все линии, связанные с идеей'''
        if idea.parent_line:
            idea.update_line_pos(idea.parent_line)

        for child_line in idea.child_lines:
            idea.update_line_pos(child_line)

        for child in idea.childs:
            self.update_all_lines_for_idea(child)

    def set_viewport_size_to_scene(self):
        '''Метод для получения размера viewport после его изменения лэйаутом'''
        viewport = self.project_window.tree_view.viewport()
        vp_size = viewport.size()
        self.setSceneRect(0, 0, vp_size.width(), vp_size.height())

    def connect_ideas(self, parent_idea: Idea, child_idea: Idea) -> bool:
        '''Метод для соединения двух идей линией'''
        if child_idea in parent_idea.childs:
            parent_rect = parent_idea.boundingRect()
            child_rect = child_idea.boundingRect()
            point1 = QPointF(parent_idea.pos().x() + parent_rect.width(),
                             parent_idea.pos().y() + parent_rect.height() - 50)
            point2 = QPointF(child_idea.pos().x(),
                             child_idea.pos().y() + child_rect.height() / 2 - 15)

            line = Line(QLineF(point1, point2), parent_idea, child_idea)
            pen = QPen(QColor(255, 255, 255))
            pen.setWidth(1)
            line.setPen(pen)
            self.addItem(line)

            parent_idea.child_lines.append(line)
            child_idea.parent_line = line

            return True
        else:
            return False

    def add_idea(self, text: str, parent_idea: Idea) -> None:
        '''Метод добавления идеи в карту мыслей'''
        child_idea = Idea(self, parent_idea.tree_row + 1, text, parent_idea)
        parent_idea.add_child(child_idea)
        self.addItem(child_idea)
        self.set_idea_pos(child_idea)
        self.connect_ideas(parent_idea, child_idea)

    def delete_idea(self, idea: Idea):
        '''Метод для удаления идеи'''
        if idea.parent_idea:
            for i in range(len(idea.childs)):
                self.delete_idea(idea.childs[i])

            idea_index = idea.parent_idea.childs.index(idea)
            helper = idea.parent_idea.childs.pop(idea_index)
            self.removeItem(idea.parent_line)
            self.removeItem(idea)
        else:
            warning_window = RootIdeaDeletionWarning()
            warning_window.exec()

    def get_allocated_idea_height(self, idea: Idea):
        '''Метод для получения высоты, отведенной одной идее'''
        if not idea.parent_idea:  # если идея корневая
            return self.height()

        parent_height = self.get_allocated_idea_height(idea.parent_idea)
        return parent_height / len(idea.parent_idea.childs)

    def set_idea_pos(self, idea: Idea):
        '''Метод для позиционирования идеи на сцене'''
        scene_height = self.height()

        if idea.parent_idea:  # если идея не корневая
            child_index = idea.parent_idea.childs.index(idea)

            x = idea.parent_idea.pos().x() + idea.parent_idea.boundingRect().width() + 20

            if child_index != 0:  # если ребенок не первый
                if idea.parent_idea.parent_idea:
                    parent_height = self.get_allocated_idea_height(idea.parent_idea)
                    parent_y = idea.parent_idea.pos().y()
                else:
                    parent_height = scene_height
                    parent_y = 0

                y = parent_y + (child_index * (parent_height /
                               len(idea.parent_idea.childs)))
            else:
                y = idea.parent_idea.pos().y()
        else:  # если корневая
            x = 0
            y = scene_height / 2

        idea.setPos(x, y)


class RootIdeaDeletionWarning(QtWidgets.QDialog):
    '''Класс виджета диалога, предупреждающего о попытке удалить корневую идею'''

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.ok_btn.pressed.connect(self.accept)

    def init_ui(self):
        self.self_layout = QtWidgets.QVBoxLayout(self)
        self.setFixedSize(270, 350)
        self.setWindowTitle("Предупреждение")

        self.image_label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("./restriction_image.jpg")
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(300, 300)
        self.self_layout.addWidget(self.image_label)

        self.label = QtWidgets.QLabel("Нельзя удалить корневую идею.", self)
        self.label.setFixedHeight(30)
        self.self_layout.addWidget(self.label)

        self.ok_btn = QtWidgets.QPushButton("OK", self)
        self.ok_btn.setFixedSize(60, 30)
        self.self_layout.addWidget(self.ok_btn)
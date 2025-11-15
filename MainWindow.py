import sys
import Consts
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication
from ProjectWindow import ProjectWindow, Task
from SQLcontroller import DBManager
from Idea_map import Idea


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projects = {}
        self.projects_names = []
        self.setup_ui(self)
        self.db_manager = DBManager(self)
        self.db_manager.load_info()
        self.sort_project_by_closest_deadline()

    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.resize(Consts.WINDOW_WIDTH, Consts.WINDOW_HEIGHT)

        self.centralwidget = QtWidgets.QWidget(parent=main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet('''
            background-color: rgb(26, 26, 26);
            color: white;
        ''')

        self.list_widget = QtWidgets.QListWidget(parent=self.centralwidget)
        self.list_widget.setGeometry(QtCore.QRect(10, 40, 781, 511))
        self.list_widget.setObjectName("listWidget")
        self.list_widget.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')

        self.add_project_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.add_project_btn.setGeometry(QtCore.QRect(10, 9, 111, 31))
        self.add_project_btn.setObjectName("addProjectBtn")
        self.add_project_btn.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.add_project_btn.pressed.connect(self.add_project)

        main_window.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(parent=main_window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        main_window.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(parent=main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.add_project_btn.setText(_translate("MainWindow", "Добавить проект"))

    def close_event(self, event):
        '''Метод для сохранения информации после закрытия'''
        self.db_manager.update_info()
        super().closeEvent(event)

    def add_project(self):
        '''Метод добавления проекта'''
        new_project_window = ProjectWindow("Новый проект", self)
        new_project_label = ProjectLabel(new_project_window, self)
        new_project_label.init_ui()
        new_project_window.project_name_label.setText(new_project_label.project_name)
        self.projects[new_project_label] = new_project_window

        new_project_item = ProjectListItem(new_project_label)
        new_project_item.setSizeHint(new_project_label.sizeHint())
        self.list_widget.addItem(new_project_item)
        self.list_widget.setItemWidget(new_project_item, new_project_label)

        new_project_label.get_project_status()
        self.sort_project_by_closest_deadline()

    def update_project_status(self, project_name):
        '''Обновление статуса конкретного проекта'''
        for i in range(self.list_widget.count()):
            project_label = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(project_label, ProjectLabel):
                project_label.get_project_status()
                break

    def create_project_from_db(self, project_name):
        '''Создание проекта при загрузке из БД'''
        new_project_window = ProjectWindow(project_name, self, True)
        new_project_label = ProjectLabel(new_project_window, self, skip_dialog=True)
        new_project_label.set_project_name(project_name)

        new_project_item = ProjectListItem(new_project_label)
        new_project_item.setSizeHint(new_project_label.sizeHint())
        self.list_widget.addItem(new_project_item)
        self.list_widget.setItemWidget(new_project_item, new_project_label)

        self.projects_names.append(project_name)
        self.projects[new_project_label] = new_project_window

        return new_project_label, new_project_window

    def sort_project_by_closest_deadline(self):
        '''Сортировка по ближайшему дедлайну'''
        self.list_widget.sortItems(QtCore.Qt.SortOrder.AscendingOrder)


class ProjectLabel(QtWidgets.QWidget):
    def __init__(self, project: ProjectWindow, main_window: MainWindow, skip_dialog=False):
        super().__init__()
        self.project = project
        self.main_window = main_window
        self.project_name = ""

        if not skip_dialog:
            self.name_selector = NameSelector(self, self.main_window)
            if self.name_selector.exec() == QtWidgets.QDialog.DialogCode.Rejected:
                # считает максимальную цифру, встречающуюся в безымянных проектах
                # нужно на случай, если например были безымянные проекты 1-6
                # и какой-то из них удалили
                max_num = 0
                for name in self.main_window.projects_names:
                    if name == "Безымянный проект":
                        max_num = max(max_num, 1)
                    elif name.startswith("Безымянный проект "):
                        try:
                            num = int(name.split()[-1])
                            max_num = max(max_num, num)
                        except ValueError:
                            pass

                if max_num == 0:
                    name = "Безымянный проект"
                else:
                    name = f"Безымянный проект {max_num + 1}"

                self.main_window.projects_names.append(name)
                self.project_name = name
        else:
            pass

    def init_ui(self):
        self.project_layout = QtWidgets.QHBoxLayout()

        self.project_name_label = QtWidgets.QLabel(self.project_name, self)
        self.project_name_label.setStyleSheet('''
            color: white;
            font-size: 16px;
        ''')
        self.project_name_label.setFixedHeight(30)
        self.project_layout.addWidget(self.project_name_label)

        self.project_status = QtWidgets.QTextBrowser(parent=self)
        self.get_project_status()

        self.project_status.setStyleSheet('''
            font-size: 16px;
        ''')
        self.project_status.setFixedSize(150, 30)
        self.project_layout.addWidget(self.project_status)

        self.link_to_project = QtWidgets.QPushButton("К проекту", self)
        self.link_to_project.setStyleSheet('''
            color: white;
            font-size: 16px;
        ''')
        self.link_to_project.setFixedSize(100, 30)
        self.project_layout.addWidget(self.link_to_project)
        self.link_to_project.pressed.connect(self.go_to_project)

        self.delete_project_btn = QtWidgets.QPushButton("x", self)
        self.delete_project_btn.setFixedSize(30, 30)
        self.delete_project_btn.setStyleSheet('''
            background-color: #c82333;
            font-size: 16px;
            color: white;
        ''')
        self.delete_project_btn.pressed.connect(self.delete_project)
        self.project_layout.addWidget(self.delete_project_btn)

        self.setLayout(self.project_layout)

    def set_project_name(self, name: str):
        '''Метод для установки имени проекта для загружаемых проектов'''
        self.project_name = name
        if name not in self.main_window.projects_names:
            self.main_window.projects_names.append(name)
        self.init_ui()

    def get_project_status(self):
        '''Метод для получения статуса проекта'''
        status = self.project.count_complete_percent()
        if status == 0:
            self.project_status.setPlainText("Запланирован")
        elif status < 100.0:
            self.project_status.setPlainText("Начат")
        else:
            self.project_status.setPlainText("Закончен")

    def go_to_project(self):
        '''Метод перехода к окну проекта'''
        self.main_window.hide()
        self.project.show()

    def delete_project(self):
        '''Метод удаления проекта'''
        project_index = 0

        for index, label in enumerate(self.main_window.projects.keys()):
            item = self.main_window.list_widget.itemWidget(
                self.main_window.list_widget.item(index))
            if isinstance(item, ProjectLabel) and item.project_name_label.text() == self.project_name_label.text():
                project_index = index
                break

        for i in range(len(self.main_window.projects_names)):
            if self.main_window.projects_names[i] == self.project_name_label.text():
                self.main_window.projects_names.pop(i)
                break

        helper = self.main_window.list_widget.takeItem(project_index)
        self.main_window.projects.pop(self)
        self.project.close()


class NameSelector(QtWidgets.QDialog):
    '''Класс для выбора названия проекта.'''

    def __init__(self, project_label: ProjectLabel, main_window: MainWindow):
        super().__init__()
        self.project_label = project_label
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(300, 150)
        self.setWindowTitle("Выберите название для проекта")

        self.selector_layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("Как назвать новый проект?", self)
        self.label.setFixedHeight(30)
        self.selector_layout.addWidget(self.label)

        self.name_setter = QtWidgets.QLineEdit(self)
        self.name_setter.setFixedHeight(30)
        self.selector_layout.addWidget(self.name_setter)

        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setFixedHeight(30)
        self.selector_layout.addWidget(self.status_label)

        self.select_name_btn = QtWidgets.QPushButton("Готово", self)
        self.select_name_btn.setFixedHeight(30)
        self.select_name_btn.setFixedWidth(80)
        self.select_name_btn.pressed.connect(self.check_name)
        self.selector_layout.addWidget(self.select_name_btn)

    def check_name(self):
        '''Метод для проверки валидности имени проекта'''
        name = self.name_setter.text()
        if name in self.main_window.projects_names:
            self.status_label.setText("Проект с таким именем уже есть")
        elif name == '' or name.count(' ') == len(name):
            self.status_label.setText("Название не может быть пустой строкой")
        elif name == "Безымянный проект" or name.startswith("Безымянный проект "):
            self.status_label.setText(
                "Это имя зарезервировано логикой приложения")
        else:
            self.main_window.projects_names.append(name)
            self.project_label.project_name = name
            self.accept()


class ProjectListItem(QtWidgets.QListWidgetItem):
    def __init__(self, project_label):
        super().__init__()
        self.project_label = project_label
        self.setSizeHint(project_label.sizeHint())

    def __lt__(self, other):
        '''Переопределение оператора < для сортировки по дедлайнам'''
        closest_deadline1 = self.project_label.project.get_closest_deadline()
        if isinstance(other, ProjectListItem):
            closest_deadline2 = other.project_label.project.get_closest_deadline()
        else:
            closest_deadline2 = None

        closest_deadline1 = closest_deadline1.toPyDate(
        ) if closest_deadline1 != None else closest_deadline1
        closest_deadline2 = closest_deadline2.toPyDate(
        ) if closest_deadline2 != None else closest_deadline2
        if closest_deadline1 and closest_deadline2:
            return closest_deadline1 < closest_deadline2
        else:
            if closest_deadline1:
                return True
            elif closest_deadline2:
                return False
            else:
                return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    ex.db_manager.update_info()
    sys.exit(app.exec())
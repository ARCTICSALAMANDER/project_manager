import string
from datetime import datetime
import Consts
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QGraphicsView
from ConsoleController import Console
from Idea_map import Idea, IdeaMap


class ProjectWindow(QMainWindow):
    def __init__(self, project_name: str, main_window, skip_default_tasks=False):
        super().__init__()
        self.project_name = project_name
        self.main_window = main_window
        self.console = Console(self)
        self.project_folder = ""
        self.setup_ui(self)

        if not skip_default_tasks:
            self.add_default_tasks()

        self.complete_percent = 0
        self.closest_deadline = ""

    def setup_ui(self, main_window):
        main_window.setObjectName("Project Manager")
        main_window.resize(Consts.WINDOW_WIDTH, Consts.WINDOW_HEIGHT)

        self.centralwidget = QtWidgets.QWidget(parent=main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet('''
            background-color: rgb(26, 26, 26);
            color: white;
        ''')

        self.console_splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.console_splitter.setGeometry(QtCore.QRect(530, 40, 256, 511))
        self.console_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.console_splitter.setObjectName("ConsoleSplitter")

        self.console_input = QtWidgets.QLineEdit(parent=self.console_splitter)
        self.console_input.setObjectName("consoleInput")
        self.console_input.insert("> ")
        self.console_input.textChanged.connect(self.restore_console_prefix)
        self.console_input.setStyleSheet('''
            background: black;
            color: white;
            font-size: 16px;
        ''')
        self.console_input.returnPressed.connect(self.execute_command)

        self.console_output = QtWidgets.QTextBrowser(
            parent=self.console_splitter)
        self.console_output.setObjectName("consoleOutput")
        self.console_output.setStyleSheet('''
            background: black;
            color: white;
            border-radius: 5px;
            font-size: 16px;
        ''')
        self.console_output.setPlainText(
            'Type "help" to see the list of existing commands')

        self.tree_check_box_cont = QtWidgets.QSplitter(parent=self.centralwidget)
        self.tree_check_box_cont.setGeometry(QtCore.QRect(20, 40, 491, 511))
        self.tree_check_box_cont.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.tree_check_box_cont.setObjectName("treeCheckBoxCont")

        self.tree_view = QGraphicsView(parent=self.tree_check_box_cont)
        self.tree_view.setObjectName("treeView")
        self.tree_view.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.idea_map = IdeaMap(self)
        self.idea_map.setSceneRect(10, 40, 400, 150)
        self.tree_view.setScene(self.idea_map)
        # разрешаем скролл
        self.tree_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree_view.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # разрешаем перетаскивать курсором
        self.tree_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.tree_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.buttons_container = QtWidgets.QWidget()
        self.buttons_layout = QtWidgets.QHBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(10)

        self.add_task_button = QtWidgets.QPushButton("Добавить задачу", self)
        self.add_task_button.setStyleSheet('''
            border: 1px solid white;
            background-color: rgb(30, 30, 30);
            border-radius: 3px;
            padding: 2px;
        ''')
        self.buttons_layout.addWidget(self.add_task_button)
        self.add_task_button.pressed.connect(self.add_task)

        self.download_tasks_btn = QtWidgets.QPushButton(
            "Скачать задачи как txt файл", parent=self.centralwidget)
        self.download_tasks_btn.setObjectName("downloadTasksBtn")
        self.download_tasks_btn.setStyleSheet('''
            border: 1px solid white;
            background-color: rgb(30, 30, 30);
            border-radius: 3px;
            padding: 2px;
        ''')
        self.download_tasks_btn.pressed.connect(self.download_tasks)
        self.buttons_layout.addWidget(self.download_tasks_btn)

        self.list_widget = QtWidgets.QListWidget(parent=self.tree_check_box_cont)
        self.list_widget.setObjectName("listWidget")
        self.list_widget.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.list_widget.setSpacing(2)

        self.tree_check_box_cont.addWidget(self.tree_view)
        self.tree_check_box_cont.addWidget(self.buttons_container)
        self.tree_check_box_cont.addWidget(self.list_widget)

        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(20, 10, 491, 21))
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")

        self.back_button = QtWidgets.QPushButton(parent=self.splitter)
        self.back_button.setObjectName("backButton")
        self.back_button.setFixedWidth(70)
        self.back_button.setStyleSheet('''
            border: 1px solid white;
            background-color: rgb(15, 15, 15);
            border-radius: 3px;
            padding: 2px;
        ''')
        self.back_button.pressed.connect(self.go_back)

        self.project_name_label = QtWidgets.QLabel(parent=self.splitter)
        self.project_name_label.setObjectName("projectName")
        self.project_name_label.setText(self.project_name)

        self.folder_path_label = QtWidgets.QTextBrowser(parent=self.splitter)
        self.folder_path_label.setObjectName("folderPath")
        self.folder_path_label.setMaximumHeight(30)
        self.folder_path_label.setPlainText(
            f"Текущая папка проекта: {self.project_folder if self.project_folder else "еще не привязана"}")

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
        main_window.setWindowTitle(_translate("MainWindow", "Project Manager"))
        self.back_button.setText(_translate("MainWindow", "<- Назад"))
        self.project_name_label.setText(
            _translate("MainWindow", self.project_name))

    def close_event(self, event):
        '''Метод для сохранения информации после закрытия'''
        self.main_window.db_manager.update_info()
        super().closeEvent(event)

    def go_back(self):
        '''Метод для перехода в главное окно'''
        self.hide()
        if self.main_window.__class__.__name__ == 'MainWindow':
            for i in range(self.main_window.list_widget.count()):
                project_label = self.main_window.list_widget.itemWidget(
                    self.main_window.list_widget.item(i))
                if project_label.project_name == self.project_name:
                    project_label.get_project_status()
                    break

        self.main_window.sort_project_by_closest_deadline()
        self.main_window.show()

    def restore_console_prefix(self):
        '''Эта функция восстанавливает префикс "> " в вводе консоли, если
        пользователь его удалит.'''
        text = self.console_input.text()
        if text[:2] != "> ":
            # это нужно, чтобы избежать рекурсивного вызова
            self.console_input.blockSignals(True)
            index = 0
            for i in range(len(text)):
                if text[i] in string.ascii_lowercase:
                    index = i
                    break

            if index > 0:  # специально для случая, если в консоли ничего нет, но пользователь нажмет бэкспейс
                self.console_input.setText("> " + text[index:])
            else:
                self.console_input.setText("> ")
            # восстанавливаем передачу сигналов
            self.console_input.blockSignals(False)

    def add_task(self, text: str = "Новая задача", is_default: bool = False):
        '''Добавление задачи в список задач'''
        task = Task(self, text, is_default)
        task_in_list = QtWidgets.QListWidgetItem()
        task_in_list.setSizeHint(task.sizeHint())
        self.list_widget.addItem(task_in_list)
        self.list_widget.setItemWidget(task_in_list, task)

    def add_default_tasks(self):
        '''Добавление стандартных задач в каждый проект'''
        self.add_task("Написать ТЗ", True)
        auto_task = self.list_widget.itemWidget(self.list_widget.item(0))

        auto_task1 = Task(self, "Создать Git-репозиторий для проекта", True)
        auto_task1_item = QtWidgets.QListWidgetItem()
        auto_task1_item.setSizeHint(auto_task1.sizeHint())
        self.list_widget.addItem(auto_task1_item)
        self.list_widget.setItemWidget(auto_task1_item, auto_task1)

        auto_task2 = Task(self, "Сделать первый коммит", True)
        auto_task2_item = QtWidgets.QListWidgetItem()
        auto_task2_item.setSizeHint(auto_task2.sizeHint())
        self.list_widget.addItem(auto_task2_item)
        self.list_widget.setItemWidget(auto_task2_item, auto_task2)

    def execute_command(self):
        '''Метод для исполнения команд через консоль'''
        self.console.command_executer()

    def get_closest_deadline(self) -> QtCore.QDate | None:
        '''Метод для получения ближайшего дедлайна. 
        Вернет None, если дедлайнов у задач вообще нет, 
        либо они все прошли, и объект типа QDate, 
        если дедлайн есть'''
        current_date = datetime.now().date()
        closest_deadline = None
        for i in range(self.list_widget.count()):
            task = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(task, Task):
                if (task.deadline != None and task.deadline.isValid()) and not task.checkbox.isChecked():
                    # Преобразуем QDate в datetime.date для сравнения
                    deadline_date = task.deadline.toPyDate()

                    # Проверяем, что дедлайн еще не прошел
                    if deadline_date >= current_date:
                        if closest_deadline is None or deadline_date < closest_deadline.toPyDate():
                            closest_deadline = task.deadline

        return closest_deadline

    def count_complete_percent(self) -> float:
        '''Метод для подсчета процента выполненных задач'''
        done_count = 0
        for i in range(self.list_widget.count()):
            item_widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(item_widget, Task):
                if item_widget.checkbox.isChecked():
                    done_count += 1

        if self.list_widget.count():
            return done_count / self.list_widget.count() * 100
        else:
            return 0.0

    def download_tasks(self):
        '''Метод для скачивания информации по задачам как файла.txt, изменит уже существующий файл есть такой есть'''
        text = f"{self.project_name} TASKS LIST\n\n"
        for i in range(self.list_widget.count()):
            task = self.list_widget.itemWidget(self.list_widget.item(i))
            if isinstance(task, Task):
                text += f"{i + 1}. {task.task_name.text()}: \n\t{f"done at {task.complete_time}" if task.checkbox.isChecked(
                ) else "not done yet"}, \n\t{task.deadline if task.deadline != None else "no deadline set"}\n"

        with open(f"{self.project_name} tasks.txt", 'w', encoding='utf-8') as f:
            f.write(text)


class Task(QtWidgets.QWidget):
    def __init__(self, project_window: ProjectWindow, task_name: str = "Новая задача", is_default: bool = False):
        super().__init__()
        self.task_layout = QtWidgets.QHBoxLayout()
        self.project_window = project_window

        self.is_default = is_default
        self.complete_time = None

        self.task_name = QtWidgets.QLineEdit(task_name, self)
        if is_default:
            self.task_name.setEnabled(False)
        self.task_name.setFixedHeight(30)
        self.task_name.setStyleSheet('''
            background-color: rgb(83, 83, 83);
            border: none;
            border-radius: 0px;
            margin: 0;
            padding: 3px;
        ''')

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setFixedHeight(30)
        self.checkbox.setStyleSheet('''
            background-color: rgb(83, 83, 83);
            border: none;
            border-radius: 0px;
            margin: 0;
            padding: 3px;
        ''')
        self.checkbox.stateChanged.connect(self.select_completing_time)
        self.checkbox.stateChanged.connect(self.set_project_status)

        self.task_layout.addWidget(self.checkbox)
        self.task_layout.addWidget(self.task_name)

        self.add_deadline_btn = QtWidgets.QPushButton("Добавить дедлайн")
        self.add_deadline_btn.setFixedWidth(120)
        self.add_deadline_btn.setFixedHeight(30)
        self.add_deadline_btn.setStyleSheet('''
            background-color: rgb(83, 83, 83);
            border: 2px solid white;
            border-radius: 0px;
            padding: 3px;
        ''')
        self.task_layout.addWidget(self.add_deadline_btn)

        self.delete_task_button = QtWidgets.QPushButton("x", self)
        self.delete_task_button.setFixedHeight(30)
        self.delete_task_button.setFixedWidth(30)
        self.delete_task_button.setStyleSheet('''
            background-color: #c82333;
            color: white;
            font-size: 20px;
        ''')
        self.delete_task_button.pressed.connect(self.delete_this_task)
        self.task_layout.addWidget(self.delete_task_button)

        self.task_layout.setSpacing(0)
        self.task_layout.setContentsMargins(3, 3, 3, 3)
        self.setLayout(self.task_layout)

        self.deadline = None
        self.calendar_widget = QtWidgets.QCalendarWidget()
        self.set_date_btn = QtWidgets.QPushButton("Выбрать эту дату")
        self.set_date_btn.clicked.connect(self.select_deadline)
        self.date_layout = QVBoxLayout()
        self.date_layout.addWidget(self.calendar_widget)
        self.date_layout.addWidget(self.set_date_btn)
        self.date_widget = QtWidgets.QWidget()
        self.date_widget.setLayout(self.date_layout)
        # показываем календарь если кнопка "Добавить дедлайн" была нажата
        self.add_deadline_btn.clicked.connect(lambda: self.date_widget.show())

    def select_deadline(self):
        '''Метод для выбора дедлайна задачи через диалоговое окно с календарем'''
        self.deadline = self.calendar_widget.selectedDate()
        self.date_widget.hide()
        self.add_deadline_btn.setText(f"До {self.deadline.toString("dd.MM.yy")}")
        self.add_deadline_btn.blockSignals(True)
        self.project_window.main_window.sort_project_by_closest_deadline()

    def set_project_status(self):
        '''Метод для выставления статуса'''
        self.project_window.main_window.update_project_status(
            self.project_window.project_name)

    def select_completing_time(self):
        '''Метод для установки времени, когда задача была выполнена'''
        if self.checkbox.isChecked():
            self.complete_time = datetime.now()

        self.project_window.main_window.update_project_status(
            self.project_window.project_name)

    def delete_this_task(self):
        '''Метод удаления задачи из списка задач'''
        if not self.is_default:
            # list_widget.count() - количество всех item у виджета
            for index in range(self.project_window.list_widget.count()):
                item = self.project_window.list_widget.item(index)
                if self.project_window.list_widget.itemWidget(item) == self:
                    self.project_window.list_widget.takeItem(index)
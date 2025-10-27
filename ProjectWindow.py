import sys
import string
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from ConsoleController import Console


class ProjectWindow(QMainWindow):
    def __init__(self, projectName: str):
        super().__init__()
        self.projectName = projectName
        self.setupUi(self)
        self.addDefaultTasks()
        self.console = Console(self)
        self.projectFolder = ""

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Project Manager")
        MainWindow.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet('''
            background-color: rgb(26, 26, 26);
            color: white;
        ''')

        self.ConsoleSplitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.ConsoleSplitter.setGeometry(QtCore.QRect(530, 40, 256, 511))
        self.ConsoleSplitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.ConsoleSplitter.setObjectName("ConsoleSplitter")

        self.consoleInput = QtWidgets.QLineEdit(parent=self.ConsoleSplitter)
        self.consoleInput.setObjectName("consoleInput")
        self.consoleInput.insert("> ")
        self.consoleInput.textChanged.connect(self.restore_console_prefix)
        self.consoleInput.setStyleSheet('''
            background: black;
            color: white;
            font-size: 16px;
        ''')
        self.consoleInput.returnPressed.connect(self.executeCommand)

        self.consoleOutput = QtWidgets.QTextBrowser(
            parent=self.ConsoleSplitter)
        self.consoleOutput.setObjectName("consoleOutput")
        self.consoleOutput.setStyleSheet('''
            background: black;
            color: white;
            border-radius: 5px;
            font-size: 16px;
        ''')
        self.consoleOutput.setPlainText(
            'Type "help" to see the list of existing commands')

        self.treeCheckBoxCont = QtWidgets.QSplitter(parent=self.centralwidget)
        self.treeCheckBoxCont.setGeometry(QtCore.QRect(20, 40, 491, 511))
        self.treeCheckBoxCont.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.treeCheckBoxCont.setObjectName("treeCheckBoxCont")

        self.treeView = QtWidgets.QTreeView(parent=self.treeCheckBoxCont)
        self.treeView.setObjectName("treeView")
        self.treeView.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.treeView.setModel(IdeaMap(self))
        self.treeView.setStyleSheet('''
            QTreeView::item{
                background-color: rgb(138, 138, 138);     
                color: white;
                font-family: sans-serif;
                font-size: 18px;                   
            }
        ''')

        self.listWidget = QtWidgets.QListWidget(parent=self.treeCheckBoxCont)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.listWidget.setSpacing(2)

        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(20, 10, 491, 21))
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")

        self.backButton = QtWidgets.QPushButton(parent=self.splitter)
        self.backButton.setObjectName("backButton")
        self.backButton.setFixedWidth(70)
        self.backButton.setStyleSheet('''
            border: 1px solid white;
            background-color: rgb(15, 15, 15);
            border-radius: 3px;
            padding: 2px;
        ''')

        self.projectNameLabel = QtWidgets.QLabel(parent=self.splitter)
        self.projectNameLabel.setObjectName("projectName")
        self.projectNameLabel.setText(self.projectName)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Project Manager"))
        self.backButton.setText(_translate("MainWindow", "<- Назад"))
        self.projectNameLabel.setText(
            _translate("MainWindow", self.projectName))

    def restore_console_prefix(self):
        '''Эта функция восстанавливает префикс "> " в вводе консоли, если
        пользователь его удалит.'''
        text = self.consoleInput.text()
        if text[:2] != "> ":
            # это нужно, чтобы избежать рекурсивного вызова
            self.consoleInput.blockSignals(True)
            index = 0
            for i in range(len(text)):
                if text[i] in string.ascii_lowercase:
                    index = i
                    break

            if index > 0:  # специально для случая, если в консоли ничего нет, но пользователь нажмет бэкспейс
                self.consoleInput.setText("> " + text[index:])
            else:
                self.consoleInput.setText("> ")
            # восстанавливаем передачу сигналов
            self.consoleInput.blockSignals(False)

    def addTask(self, taskName: str):
        '''Добавление задачи в список задач'''
        task = Task(taskName)
        taskInList = QtWidgets.QListWidgetItem()
        taskInList.setSizeHint(task.sizeHint())
        self.listWidget.addItem(taskInList)
        self.listWidget.setItemWidget(taskInList, task)

    def deleteTask(self, taskNumber: int) -> bool:
        '''Удаление задачи из списка по номеру'''
        helper = self.listWidget.takeItem(taskNumber - 1)
        if helper == None:
            return False
        else:
            return True

    def addDefaultTasks(self):
        '''Добавление стандартных задач в каждый проект'''
        self.addTask("Написать ТЗ")

        auto_task1 = Task("Создать Git-репозиторий для проекта")
        auto_task1_item = QtWidgets.QListWidgetItem()
        auto_task1_item.setSizeHint(auto_task1.sizeHint())
        self.listWidget.addItem(auto_task1_item)
        self.listWidget.setItemWidget(auto_task1_item, auto_task1)

        auto_task2 = Task("Сделать первый коммит")
        auto_task2_item = QtWidgets.QListWidgetItem()
        auto_task2_item.setSizeHint(auto_task2.sizeHint())
        self.listWidget.addItem(auto_task2_item)
        self.listWidget.setItemWidget(auto_task2_item, auto_task2)

    def executeCommand(self):
        self.console.commandExecuter()


class Task(QtWidgets.QWidget):
    def __init__(self, taskName: str):
        super().__init__()
        self.taskName = taskName

        self.taskLayout = QtWidgets.QHBoxLayout()

        self.checkbox = QtWidgets.QCheckBox(taskName)
        self.checkbox.setFixedHeight(30)
        self.checkbox.setStyleSheet('''
            background-color: rgb(83, 83, 83);
        ''')
        self.taskLayout.addWidget(self.checkbox)

        self.addDeadlineBtn = QtWidgets.QPushButton("Добавить дедлайн")
        self.addDeadlineBtn.setFixedWidth(120)
        self.addDeadlineBtn.setFixedHeight(30)
        self.addDeadlineBtn.setStyleSheet('''
            background-color: rgb(83, 83, 83);
        ''')
        self.taskLayout.addWidget(self.addDeadlineBtn)
        self.setLayout(self.taskLayout)

        self.calendarWidget = QtWidgets.QCalendarWidget()
        self.setDateBtn = QtWidgets.QPushButton("Выбрать эту дату")
        self.setDateBtn.clicked.connect(self.selectDeadline)
        self.dateLayout = QVBoxLayout()
        self.dateLayout.addWidget(self.calendarWidget)
        self.dateLayout.addWidget(self.setDateBtn)
        self.dateWidget = QtWidgets.QWidget()
        self.dateWidget.setLayout(self.dateLayout)
        # показываем календарь если кнопка "Добавить дедлайн" была нажата
        self.addDeadlineBtn.clicked.connect(lambda: self.dateWidget.show())

    def selectDeadline(self):
        self.deadline = self.calendarWidget.selectedDate()
        self.dateWidget.hide()
        self.addDeadlineBtn.setText(f"До {self.deadline.toString("dd.MM.yy")}")
        self.addDeadlineBtn.blockSignals(True)


class Idea(QStandardItem):
    '''Класс идеи'''

    def __init__(self, text: str, parentIdea=None):
        super().__init__(text)
        self.parentIdea = parentIdea
        self.childs = []

    def addChild(self, child) -> bool:
        '''Метод добавления дочерней мысли'''
        if isinstance(child, Idea):
            self.childs.append(child)
            return True
        else:
            return False


class IdeaMap(QStandardItemModel):
    '''Класс карты мыслей'''

    def __init__(self, projectWindow: ProjectWindow):
        super().__init__(projectWindow.treeView)
        self.rootIdea = Idea("Первая мысль")
        self.appendRow(self.rootIdea)

    def addIdea(self, text: str, parentIdea: Idea):
        '''Метод добавления идеи в карту мыслей'''
        parentIdea.childs.append(Idea(text, parentIdea))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProjectWindow("New Project")
    ex.show()
    sys.exit(app.exec())

import sys
import string
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout


class ProjectWindow(QMainWindow):
    def __init__(self, projectName):
        super().__init__()
        self.setupUi(self)
        self.projectName = projectName

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
        ''')

        self.consoleOutput = QtWidgets.QTextBrowser(parent=self.ConsoleSplitter)
        self.consoleOutput.setObjectName("consoleOutput")
        self.consoleOutput.setStyleSheet('''
            background: black;
            color: white;
            border-radius: 5px;
        ''')

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

        self.projectName = QtWidgets.QLabel(parent=self.splitter)
        self.projectName.setObjectName("projectName")

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
        self.projectName.setText(_translate("MainWindow", "TextLabel"))

    def restore_console_prefix(self):
        '''Эта функция восстанавливает префикс "> " в вводе консоли, если
        пользователь его удалит.'''
        text = self.consoleInput.text()
        if text[:2] != "> ":
            self.consoleInput.blockSignals(True) # это нужно, чтобы избежать рекурсивного вызова
            index = 0
            for i in range(len(text)):
                if text[i] in string.ascii_lowercase:
                    index = i
                    break
            
            if index > 0: # специально для случая, если в консоли ничего нет, но пользователь нажмет бэкспейс
                self.consoleInput.setText("> " + text[index:])
            else:
                self.consoleInput.setText("> ")
            self.consoleInput.blockSignals(False) # восстанавливаем передачу сигналов

    def add_task(self, taskName: str):
        '''Добавление задачи в список задач'''
        task = Task(taskName)
        taskInList = QtWidgets.QListWidgetItem()
        taskInList.setSizeHint(task.sizeHint())
        self.listWidget.addItem(taskInList)
        self.listWidget.setItemWidget(taskInList, task)


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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProjectWindow("New Project")
    ex.show()
    sys.exit(app.exec())

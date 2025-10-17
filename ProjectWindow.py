import sys
import string
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication


class ProjectWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

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

        self.listWidget = QtWidgets.QListWidget(parent=self.treeCheckBoxCont)
        self.listWidget.setObjectName("listWidget")

        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setGeometry(QtCore.QRect(20, 10, 491, 21))
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")

        self.backButton = QtWidgets.QPushButton(parent=self.splitter)
        self.backButton.setObjectName("backButton")

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
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProjectWindow()
    ex.show()
    sys.exit(app.exec())

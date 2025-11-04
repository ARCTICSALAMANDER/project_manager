import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication
from ProjectWindow import ProjectWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projects = {}
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet('''
            background-color: rgb(26, 26, 26);
            color: white;
        ''')

        self.listWidget = QtWidgets.QListWidget(parent=self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(10, 40, 781, 511))
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')

        self.addProjectBtn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.addProjectBtn.setGeometry(QtCore.QRect(10, 9, 111, 31))
        self.addProjectBtn.setObjectName("addProjectBtn")
        self.addProjectBtn.setStyleSheet('''
            background-color: rgb(15, 15, 15);
            border: 1px solid white;
            border-radius: 5px;
            color: white;
        ''')
        self.addProjectBtn.pressed.connect(self.addProject)

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
        self.addProjectBtn.setText(_translate("MainWindow", "Добавить проект"))

    def addProject(self):
        '''Метод добавления проекта'''
        newProjectWindow = ProjectWindow("Новый проект", self)
        newProjectLabel = ProjectLabel(newProjectWindow, self)
        newProjectLabel.initUi()
        self.projects[newProjectLabel] = newProjectWindow
        newProjectItem = QtWidgets.QListWidgetItem()
        newProjectItem.setSizeHint(newProjectLabel.sizeHint())
        self.listWidget.addItem(newProjectItem)
        self.listWidget.setItemWidget(newProjectItem, newProjectLabel)


class ProjectLabel(QtWidgets.QWidget):
    def __init__(self, project: ProjectWindow, mainWindow: MainWindow):
        super().__init__()
        self.project = project
        self.mainWindow = mainWindow
        
    def initUi(self):
        self.projectLayout = QtWidgets.QHBoxLayout()
        
        self.projectLabel = QtWidgets.QLineEdit(self.project.projectName, self)
        self.projectLabel.setStyleSheet('''
            color: white;
            font-size: 16px;
        ''')
        self.projectLabel.setFixedHeight(30)
        self.projectLayout.addWidget(self.projectLabel)

        self.projectStatus = QtWidgets.QTextBrowser(parent=self)
        self.getProjectStatus()

        self.projectStatus.setStyleSheet('''
            font-size: 16px;
        ''')
        self.projectStatus.setFixedSize(150, 30)
        self.projectLayout.addWidget(self.projectStatus)

        self.linkToProject = QtWidgets.QPushButton("К проекту", self)
        self.linkToProject.setStyleSheet('''
            color: white;
            font-size: 16px;
        ''')
        self.linkToProject.setFixedSize(100, 30)
        self.projectLayout.addWidget(self.linkToProject)
        self.linkToProject.pressed.connect(self.goToProject)

        self.deleteProjectBtn = QtWidgets.QPushButton("x", self)
        self.deleteProjectBtn.setFixedSize(30, 30)
        self.deleteProjectBtn.setStyleSheet('''
            background-color: #c82333;
            font-size: 16px;
            color: white;
        ''')
        self.deleteProjectBtn.pressed.connect(self.deleteProject)
        self.projectLayout.addWidget(self.deleteProjectBtn)

        self.setLayout(self.projectLayout)

    def getProjectStatus(self):
        '''Метод для получения статуса проекта'''
        status = self.project.countCompletePercent()
        if status == 0:
            self.projectStatus.setPlainText("Запланирован")
        elif status < 100.0:
            self.projectStatus.setPlainText("Начат")
        else:
            self.projectStatus.setPlainText("Закончен")

    def goToProject(self):
        '''Метод перехода к окну проекта'''
        self.mainWindow.hide()
        self.project.show()

    def deleteProject(self):
        '''Метод удаления проекта'''
        projectIndex = 0

        for index, label in enumerate(self.mainWindow.projects.keys()):
            if self.mainWindow.projects[label] == self.project:
                projectIndex = index
                break

        self.mainWindow.listWidget.takeItem(projectIndex)
        self.mainWindow.projects.pop(self)
        self.project.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())

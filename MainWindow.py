import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication
from ProjectWindow import ProjectWindow, Task
from SQLcontroller import DBManager
from Idea_map import Idea


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projects = {}
        self.projectsNames = []
        self.setupUi(self)
        self.DBManager = DBManager(self)
        self.DBManager.loadInfo()
        self.sortProjectByClosestDeadline()

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

    def closeEvent(self, event):
        '''Метод для сохранения информации после закрытия'''
        self.DBManager.updateInfo()
        super().closeEvent(event)

    def addProject(self):
        '''Метод добавления проекта'''
        newProjectWindow = ProjectWindow("Новый проект", self)
        newProjectLabel = ProjectLabel(newProjectWindow, self)
        newProjectLabel.initUi()
        newProjectWindow.projectNameLabel.setText(newProjectLabel.projectName)
        self.projects[newProjectLabel] = newProjectWindow

        newProjectItem = ProjectListItem(newProjectLabel)
        newProjectItem.setSizeHint(newProjectLabel.sizeHint())
        self.listWidget.addItem(newProjectItem)
        self.listWidget.setItemWidget(newProjectItem, newProjectLabel)

        newProjectLabel.getProjectStatus()
        self.sortProjectByClosestDeadline()

    def updateProjectStatus(self, project_name):
        '''Обновление статуса конкретного проекта'''
        for i in range(self.listWidget.count()):
            projectLabel = self.listWidget.itemWidget(self.listWidget.item(i))
            if isinstance(projectLabel, ProjectLabel):
                projectLabel.getProjectStatus()
                break

    def createProjectFromDB(self, project_name):
        '''Создание проекта при загрузке из БД'''
        newProjectWindow = ProjectWindow(project_name, self, True)
        newProjectLabel = ProjectLabel(newProjectWindow, self, skipDialog=True)
        newProjectLabel.setProjectName(project_name)
        
        newProjectItem = ProjectListItem(newProjectLabel)
        newProjectItem.setSizeHint(newProjectLabel.sizeHint())
        self.listWidget.addItem(newProjectItem)
        self.listWidget.setItemWidget(newProjectItem, newProjectLabel)

        self.projectsNames.append(project_name)
        self.projects[newProjectLabel] = newProjectWindow
        
        return newProjectLabel, newProjectWindow
        
    def sortProjectByClosestDeadline(self):
        '''Сортировка по ближайшему дедлайну'''
        self.listWidget.sortItems(QtCore.Qt.SortOrder.AscendingOrder)


class ProjectLabel(QtWidgets.QWidget):
    def __init__(self, project: ProjectWindow, mainWindow: MainWindow, skipDialog=False):
        super().__init__()
        self.project = project
        self.mainWindow = mainWindow
        self.projectName = ""

        if not skipDialog:
            self.nameSelector = NameSelector(self, self.mainWindow)
            if self.nameSelector.exec() == QtWidgets.QDialog.DialogCode.Rejected:
                # считает максимальную цифру, встречающуюся в безымянных проектах
                # нужно на случай, если например были безымянные проекты 1-6
                # и какой-то из них удалили
                max_num = 0
                for name in self.mainWindow.projectsNames:
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

                self.mainWindow.projectsNames.append(name)
                self.projectName = name
        else:
            pass

    def initUi(self):
        self.projectLayout = QtWidgets.QHBoxLayout()

        self.projectNameLabel = QtWidgets.QLabel(self.projectName, self)
        self.projectNameLabel.setStyleSheet('''
            color: white;
            font-size: 16px;
        ''')
        self.projectNameLabel.setFixedHeight(30)
        self.projectLayout.addWidget(self.projectNameLabel)

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

    def setProjectName(self, name: str):
        '''Метод для установки имени проекта для загружаемых проектов'''
        self.projectName = name
        if name not in self.mainWindow.projectsNames:
            self.mainWindow.projectsNames.append(name)
        self.initUi()

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
            item = self.mainWindow.listWidget.itemWidget(
                self.mainWindow.listWidget.item(index))
            if isinstance(item, ProjectLabel) and item.projectNameLabel.text() == self.projectNameLabel.text():
                projectIndex = index
                break

        for i in range(len(self.mainWindow.projectsNames)):
            if self.mainWindow.projectsNames[i] == self.projectNameLabel.text():
                self.mainWindow.projectsNames.pop(i)
                break

        helper = self.mainWindow.listWidget.takeItem(projectIndex)
        self.mainWindow.projects.pop(self)
        self.project.close()


class NameSelector(QtWidgets.QDialog):
    '''Класс для выбора названия проекта.'''

    def __init__(self, projectLabel: ProjectLabel, mainWindow: MainWindow):
        super().__init__()
        self.projectLabel = projectLabel
        self.mainWindow = mainWindow
        self.initUi()

    def initUi(self):
        self.setFixedSize(300, 150)
        self.setWindowTitle("Выберите название для проекта")

        self.selectorLayout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("Как назвать новый проект?", self)
        self.label.setFixedHeight(30)
        self.selectorLayout.addWidget(self.label)

        self.nameSetter = QtWidgets.QLineEdit(self)
        self.nameSetter.setFixedHeight(30)
        self.selectorLayout.addWidget(self.nameSetter)

        self.statusLabel = QtWidgets.QLabel("", self)
        self.statusLabel.setFixedHeight(30)
        self.selectorLayout.addWidget(self.statusLabel)

        self.selectNameBtn = QtWidgets.QPushButton("Готово", self)
        self.selectNameBtn.setFixedHeight(30)
        self.selectNameBtn.setFixedWidth(80)
        self.selectNameBtn.pressed.connect(self.checkName)
        self.selectorLayout.addWidget(self.selectNameBtn)

    def checkName(self):
        '''Метод для проверки валидности имени проекта'''
        name = self.nameSetter.text()
        if name in self.mainWindow.projectsNames:
            self.statusLabel.setText("Проект с таким именем уже есть")
        elif name == '' or name.count(' ') == len(name):
            self.statusLabel.setText("Название не может быть пустой строкой")
        elif name == "Безымянный проект" or name.startswith("Безымянный проект "):
            self.statusLabel.setText(
                "Это имя зарезервировано логикой приложения")
        else:
            self.mainWindow.projectsNames.append(name)
            self.projectLabel.projectName = name
            self.accept()


class ProjectListItem(QtWidgets.QListWidgetItem):
    def __init__(self, projectLabel):
        super().__init__()
        self.projectLabel = projectLabel
        self.setSizeHint(projectLabel.sizeHint())
        
    def __lt__(self, other):
        '''Переопределение оператора < для сортировки по дедлайнам'''
        closestDeadline1 = self.projectLabel.project.getClosestDeadline()
        if isinstance(other, ProjectListItem):
            closestDeadline2 = other.projectLabel.project.getClosestDeadline()
        else:
            closestDeadline2 = None

        closestDeadline1 = closestDeadline1.toPyDate() if closestDeadline1 != None else closestDeadline1
        closestDeadline2 = closestDeadline2.toPyDate() if closestDeadline2 != None else closestDeadline2
        if closestDeadline1 and closestDeadline2:
            return closestDeadline1 < closestDeadline2
        else:
            if closestDeadline1:
                return True
            elif closestDeadline2:
                return False
            else:
                return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    ex.DBManager.updateInfo()
    sys.exit(app.exec())

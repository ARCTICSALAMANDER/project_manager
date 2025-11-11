import sqlite3
from PyQt6.QtWidgets import QListWidget, QListWidgetItem


class DBManager:
    def __init__(self, mainWindow, MainWindowClass, ProjectWindowClass, ProjectLabelClass, TaskClass, ideaClass):
        self.mainWindow = mainWindow
        self.mainWindowClass = MainWindowClass
        self.projectWindowClass = ProjectWindowClass
        self.projectLabelClass = ProjectLabelClass
        self.taskClass = TaskClass
        self.ideaClass = ideaClass

        self.con = sqlite3.connect("ProjectManagerDB.sqlite")
        self.cur = self.con.cursor()
        try:
            status = self.cur.execute('''
                CREATE TABLE IF NOT EXISTS ProjectsList (projectID INTEGER PRIMARY KEY, project TEXT NOT NULL, projectFolder TEXT);''')

            status = self.cur.execute('''
                CREATE TABLE IF NOT EXISTS Tasks (taskID INTEGER PRIMARY KEY AUTOINCREMENT, projectID INTEGER NOT NULL, task TEXT NOT NULL, isDone NUMERIC, deadline TEXT, isDefault NUMERIC, completeTime TEXT, FOREIGN KEY(projectID) REFERENCES ProjectsList(projectID))
            ''')

            # parent_id - ссылка на родительскую идею
            # tree_row - уровень вложенности
            # position - порядок среди "сестер"
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    project_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    tree_row INTEGER,
                    position INTEGER,
                    x_pos REAL,
                    y_pos REAL,
                    FOREIGN KEY (parent_id) REFERENCES ideas (id)             
                )
            ''')
        except sqlite3.OperationalError as e:
            print(e)

    def updateInfo(self):
        '''Метод обновления информации в БД после закрытия приложения'''
        self.cur.execute("DELETE FROM ProjectsList")
        self.cur.execute("DELETE FROM Tasks")
        self.cur.execute("DELETE FROM ideas")

        # чтобы не было проблем с последовательностью импортов
        if self.mainWindow.__class__.__name__ == 'MainWindow':
            for i in range(self.mainWindow.listWidget.count()):
                projectLabel = self.mainWindow.listWidget.itemWidget(
                    self.mainWindow.listWidget.item(i))

                if projectLabel.__class__.__name__ == 'ProjectLabel':
                    self.cur.execute(
                        '''INSERT INTO ProjectsList (projectID, project, projectFolder) VALUES (?, ?, ?)''', (i, projectLabel.projectName, projectLabel.project.projectFolder))

                    for j in range(projectLabel.project.listWidget.count()):
                        task = projectLabel.project.listWidget.itemWidget(
                            projectLabel.project.listWidget.item(j))
                        if task.__class__.__name__ == 'Task':
                            deadline = None
                            if task.deadline:
                                deadline = task.deadline.toPyDate().strftime("%d-%m-%Y")

                            self.cur.execute('''
                                INSERT INTO Tasks (projectID, task, isDone, deadline, isDefault, completeTime) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (i, task.taskName.text(), task.checkbox.isChecked(), deadline, task.isDefault, task.completeTime))

            self.saveIdeas()

        self.con.commit()

    def saveIdeas(self):
        for i in range(self.mainWindow.listWidget.count()):
            projectLabel = self.mainWindow.listWidget.itemWidget(
                self.mainWindow.listWidget.item(i))
            
            projectId = self.cur.execute('''
                SELECT projectId FROM ProjectsList
                WHERE project = ?
            ''', (projectLabel.projectName,)).fetchall()

            rootIdea = projectLabel.project.ideaMap.rootIdea
            self.cur.execute('''
                INSERT INTO ideas (parent_id, project_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (0, projectId[0][0], rootIdea.textEdit.text(), rootIdea.treeRow, 0, rootIdea.pos().x(), rootIdea.pos().y()))

            parentId = self.cur.lastrowid  # значение последней колонки

            for j in range(len(rootIdea.childs)):
                self.saveIdea(rootIdea.childs[j], parentId, projectId[0][0], j)

        self.con.commit()

    def saveIdea(self, idea, parentId, projectId, position):
        '''Метод для рекурсивного сохранения идей'''
        self.cur.execute('''
            INSERT INTO ideas (parent_id, project_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (parentId, projectId, idea.textEdit.text(), idea.treeRow, position, idea.pos().x(), idea.pos().y()))

        currentId = self.cur.lastrowid

        for i in range(len(idea.childs)):
            self.saveIdea(idea.childs[i], currentId, projectId, i)

    def loadInfo(self):
        projects = self.cur.execute('''
            SELECT project, projectId FROM ProjectsList
        ''').fetchall()

        for i in range(len(projects)):
            newProjectLabel, newProjectWindow = self.createProject(projects[i][0])
            self.loadTasks(projects[i][1], newProjectLabel)
            self.loadIdeas(newProjectWindow, projects[i][1])

    def createProject(self, projectName: str):
        '''Метод для создания одного проекта, привяжет папку'''
        newProjectWindow = self.projectWindowClass(
            projectName, self.mainWindow)
        newProjectLabel = self.projectLabelClass(
            newProjectWindow, self.mainWindow, skipDialog=True)

        newProjectLabel.setProjectName(projectName)

        newProjectLabelItem = QListWidgetItem()
        newProjectLabelItem.setSizeHint(newProjectLabel.sizeHint())
        self.mainWindow.listWidget.addItem(newProjectLabelItem)
        self.mainWindow.listWidget.setItemWidget(
            newProjectLabelItem, newProjectLabel)

        self.mainWindow.projectsNames.append(projectName)
        self.mainWindow.projects[newProjectLabel] = newProjectWindow

        newProjectFolder = self.cur.execute('''
            SELECT projectFolder FROM ProjectsList
            WHERE project = ?
        ''', (projectName,)).fetchall()[0][0]
        if newProjectFolder:
            newProjectWindow.projectFolder = newProjectFolder
            status = newProjectWindow.console.bindFolder(
                f"bind_folder {newProjectFolder}", 11)

        return newProjectLabel, newProjectWindow

    def loadTasks(self, projectId: int, projectLabel):
        '''Метод для загрузки задач'''
        tasks = self.cur.execute(
            '''SELECT isDefault, taskId FROM Tasks
            WHERE projectId = ?''', (projectId,)).fetchall()

        for i in range(len(tasks)):
            if tasks[i][0] == 1:
                task = projectLabel.project.listWidget.itemWidget(
                    projectLabel.project.listWidget.item(i))
            else:
                task = self.taskClass(projectLabel.project)

            if isinstance(task, self.taskClass):
                taskName = self.cur.execute('''
                    SELECT task FROM tasks
                    WHERE projectId = ? AND taskId = ?
                ''', (projectId, tasks[i][1])).fetchall()
                task.taskName.setText(taskName[0][0])

                isChecked = self.cur.execute('''
                        SELECT isDone FROM Tasks
                        WHERE taskId = ? AND projectId = ?
                ''', (tasks[i][1], projectId)).fetchall()
                if isChecked[0][0] == 1:
                    task.checkbox.setChecked(True)
                deadline = self.cur.execute('''
                    SELECT deadline FROM tasks
                    WHERE taskId = ? AND projectId = ?
                ''', (tasks[i][1], projectId)).fetchall()
                if deadline[0][0]:
                    task.addDeadlineBtn.setText(
                        f"До {deadline[0][0].replace('-', '.')}")
                    task.addDeadlineBtn.blockSignals(True)

    def loadIdeas(self, project, projectId: int):
        rootIdea = project.ideaMap.rootIdea
        rootIdeaText = self.cur.execute(
            '''SELECT text FROM ideas
               WHERE project_id = ? AND parent_id = 0
            ''', (projectId,)
        ).fetchall()
        rootIdea.textEdit.setText(rootIdeaText[0][0])

        rootIdeaPos = self.cur.execute('''
            SELECT x_pos, y_pos FROM ideas
            WHERE project_id = ? AND parent_id = 0
        ''', (projectId,)).fetchall()
        rootIdea.setPos(rootIdeaPos[0][0], rootIdeaPos[0][1])

        rootIdeaId = self.cur.execute('''
            SELECT id FROM ideas
            WHERE project_id = ? AND tree_row = 0
        ''', (projectId,)).fetchall()[0][0]

        rootIdeaChildCount = len(self.cur.execute('''
            SELECT id FROM ideas
            WHERE parent_id = ? AND project_id = ?
        ''', (rootIdeaId, projectId)).fetchall())

        for i in range(rootIdeaChildCount):
            self.loadIdea(project, projectId, rootIdea, rootIdeaId, i)

    def loadIdea(self, project, projectId: int, parentIdea, parentId: int, position: int):
        '''Метод для загрузки одной идеи и ее детей'''
        ideasInfo = self.cur.execute(
            '''SELECT text, x_pos, y_pos, tree_row, id FROM ideas
            WHERE parent_id = ?''', (parentId,)
        ).fetchall()

        for i in range(len(ideasInfo)):
            idea = self.ideaClass(project.ideaMap, ideasInfo[i][3], ideasInfo[i][0], parentIdea)
            parentIdea.addChild(idea)
            project.ideaMap.addItem(idea)
            idea.setPos(ideasInfo[i][1], ideasInfo[i][2])
            project.ideaMap.connectIdeas(parentIdea, idea)

            ideaId = ideasInfo[i][4]

            ideaChildrenCount = len(self.cur.execute('''
                SELECT text FROM ideas
                WHERE parent_id = ?
            ''', (ideaId,)).fetchall())

            for j in range(ideaChildrenCount):
                if ideaId:
                    self.loadIdea(project, projectId, idea, ideaId, j)




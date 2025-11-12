import sqlite3
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6 import QtCore


class DBManager:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow
        self.con = sqlite3.connect("ProjectManagerDB.sqlite")
        self.cur = self.con.cursor()
        try:
            status = self.cur.execute('''
                CREATE TABLE IF NOT EXISTS ProjectsList (projectID INTEGER PRIMARY KEY, project TEXT NOT NULL, projectFolder TEXT);''')

            status = self.cur.execute('''
                CREATE TABLE IF NOT EXISTS Tasks (taskID INTEGER PRIMARY KEY AUTOINCREMENT, projectID INTEGER NOT NULL, task TEXT NOT NULL, isDone NUMERIC, deadline TEXT, isDefault NUMERIC, completeTime TEXT, FOREIGN KEY(projectID) REFERENCES ProjectsList(projectID))
            ''')

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

        if self.mainWindow.__class__.__name__ == 'MainWindow':
            for i in range(self.mainWindow.listWidget.count()):
                projectLabel = self.mainWindow.listWidget.itemWidget(
                    self.mainWindow.listWidget.item(i))

                if projectLabel.__class__.__name__ == 'ProjectLabel':
                    self.cur.execute(
                        '''INSERT INTO ProjectsList (projectID, project, projectFolder) VALUES (?, ?, ?)''', 
                        (i, projectLabel.projectName, projectLabel.project.projectFolder))

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
            
            projectId_result = self.cur.execute('''
                SELECT projectID FROM ProjectsList
                WHERE project = ?
            ''', (projectLabel.projectName,)).fetchone()
            
            if projectId_result:
                projectId = projectId_result[0]
                rootIdea = projectLabel.project.ideaMap.rootIdea
                
                self.cur.execute('''
                    INSERT INTO ideas (parent_id, project_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (0, projectId, rootIdea.textEdit.text(), rootIdea.treeRow, 0, rootIdea.pos().x(), rootIdea.pos().y()))

                parentId = self.cur.lastrowid

                for j in range(len(rootIdea.childs)):
                    self.saveIdea(rootIdea.childs[j], parentId, projectId, j)

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
        '''Загрузка данных из БД - теперь используем существующие методы mainWindow'''
        projects = self.cur.execute('''
            SELECT project, projectID FROM ProjectsList
        ''').fetchall()

        for project_name, project_id in projects:
            if hasattr(self.mainWindow, 'createProjectFromDB'):
                newProjectLabel, newProjectWindow = self.mainWindow.createProjectFromDB(project_name)
                self.loadTasks(project_id, newProjectLabel)
                self.loadIdeas(newProjectWindow, project_id)

    def loadTasks(self, projectId: int, projectLabel):
        '''Метод для загрузки задач'''
        tasks = self.cur.execute(
            '''SELECT task, isDone, deadline, isDefault, taskID FROM Tasks
            WHERE projectID = ? ORDER BY taskID''', (projectId,)).fetchall()

        for task_text, is_done, deadline_str, is_default, task_id in tasks:
            projectLabel.project.addTask(task_text, is_default)
            
            last_index = projectLabel.project.listWidget.count() - 1
            if last_index >= 0:
                task = projectLabel.project.listWidget.itemWidget(
                    projectLabel.project.listWidget.item(last_index))
                
                if is_done:
                    task.checkbox.setChecked(True)
                
                if deadline_str:
                    task.addDeadlineBtn.setText(f"До {deadline_str.replace('-', '.')}")
                    task.deadline = QtCore.QDate(int(deadline_str[:2]), int(deadline_str[3:5]), int(deadline_str[6:]))
                    task.addDeadlineBtn.blockSignals(True)

        projectLabel.getProjectStatus()

    def loadIdeas(self, project, projectId: int):
        '''Загрузка идей - упрощенная версия'''
        try:
            root_data = self.cur.execute(
                '''SELECT text, x_pos, y_pos, id FROM ideas
                WHERE project_id = ? AND parent_id = 0''', (projectId,)
            ).fetchone()
            
            if root_data:
                root_text, root_x, root_y, root_id = root_data
                rootIdea = project.ideaMap.rootIdea
                rootIdea.textEdit.setText(root_text)
                rootIdea.setPos(root_x, root_y)
                
                self._loadChildIdeas(project, projectId, rootIdea, root_id)
                
        except Exception as e:
            print(f"Error loading ideas: {e}")

    def _loadChildIdeas(self, project, projectId: int, parentIdea, parentDbId: int):
        '''Рекурсивная загрузка дочерних идей'''
        child_ideas = self.cur.execute(
            '''SELECT text, x_pos, y_pos, tree_row, id FROM ideas
            WHERE project_id = ? AND parent_id = ?''', (projectId, parentDbId)
        ).fetchall()

        for text, x_pos, y_pos, tree_row, idea_id in child_ideas:
            project.ideaMap.addIdea(text, parentIdea)
            
            if parentIdea.childs:
                child_idea = parentIdea.childs[-1]
                child_idea.setPos(x_pos, y_pos)
                
                self._loadChildIdeas(project, projectId, child_idea, idea_id)
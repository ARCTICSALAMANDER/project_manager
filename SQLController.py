import sqlite3


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

            # parent_id - ссылка на родительскую идею
            # tree_row - уровень вложенности
            # position - порядок среди "сестер"
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
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

        if self.mainWindow.__class__.__name__ == 'MainWindow': # чтобы не было проблем с последовательностью импортов
            for i in range(self.mainWindow.listWidget.count()):
                projectLabel = self.mainWindow.listWidget.itemWidget(
                    self.mainWindow.listWidget.item(i))
                
                if projectLabel.__class__.__name__ == 'ProjectLabel':
                    self.cur.execute(
                        '''INSERT INTO ProjectsList (projectID, project, projectFolder) VALUES (?, ?, ?)''', (i, projectLabel.projectName, projectLabel.project.projectFolder))
                
                    for j in range(projectLabel.project.listWidget.count()):
                        task = projectLabel.project.listWidget.itemWidget(projectLabel.project.listWidget.item(j))
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
            projectLabel = self.mainWindow.listWidget.itemWidget(self.mainWindow.listWidget.item(i))

            rootIdea = projectLabel.project.ideaMap.rootIdea
            self.cur.execute('''
                INSERT INTO ideas (parent_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?)
            ''', (0, rootIdea.textEdit.text(), rootIdea.treeRow, 0, rootIdea.pos().x(), rootIdea.pos().y()))

            parentId = self.cur.lastrowid # значение последней колонки

            for j in range(len(rootIdea.childs)):
                self.saveIdea(rootIdea.childs[j], parentId, j)

        self.con.commit()
                
    def saveIdea(self, idea, parentId, position):
        '''Метод для рекурсивного сохранения идей'''
        print(f"Сохраняем идею: {idea.textEdit.text()}")

        self.cur.execute('''
            INSERT INTO ideas (parent_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?)
        ''', (parentId, idea.textEdit.text(), idea.treeRow, position, idea.pos().x(), idea.pos().y()))

        currentId = self.cur.lastrowid

        for i in range(len(idea.childs)):
            self.saveIdea(idea.childs[i], currentId, i)


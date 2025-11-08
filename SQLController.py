import sqlite3


class SqlController:
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
        except sqlite3.OperationalError as e:
            print(e)

    def updateInfo(self):
        '''Метод обновления информации в БД после закрытия приложения'''
        self.cur.execute("DELETE FROM ProjectsList")
        self.cur.execute("DELETE FROM Tasks")      

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
        self.con.commit()

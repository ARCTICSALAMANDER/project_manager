import sqlite3
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6 import QtCore


class DBManager:
    def __init__(self, main_window):
        self.main_window = main_window
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

    def update_info(self):
        '''Метод обновления информации в БД после закрытия приложения'''
        self.cur.execute("DELETE FROM ProjectsList")
        self.cur.execute("DELETE FROM Tasks")
        self.cur.execute("DELETE FROM ideas")

        if self.main_window.__class__.__name__ == 'MainWindow':
            for i in range(self.main_window.list_widget.count()):
                project_label = self.main_window.list_widget.itemWidget(
                    self.main_window.list_widget.item(i))

                if project_label.__class__.__name__ == 'ProjectLabel':
                    self.cur.execute(
                        '''INSERT INTO ProjectsList (projectID, project, projectFolder) VALUES (?, ?, ?)''',
                        (i, project_label.project_name, project_label.project.project_folder))

                    for j in range(project_label.project.list_widget.count()):
                        task = project_label.project.list_widget.itemWidget(
                            project_label.project.list_widget.item(j))
                        if task.__class__.__name__ == 'Task':
                            deadline = None
                            if task.deadline:
                                deadline = task.deadline.toPyDate().strftime("%d-%m-%Y")

                            self.cur.execute('''
                                INSERT INTO Tasks (projectID, task, isDone, deadline, isDefault, completeTime) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (i, task.task_name.text(), task.checkbox.isChecked(), deadline, task.is_default, task.complete_time))

            self.save_ideas()

        self.con.commit()

    def save_ideas(self):
        '''Сохранение идей в БД'''
        for i in range(self.main_window.list_widget.count()):
            project_label = self.main_window.list_widget.itemWidget(
                self.main_window.list_widget.item(i))

            project_id_result = self.cur.execute('''
                SELECT projectID FROM ProjectsList
                WHERE project = ?
            ''', (project_label.project_name,)).fetchone()

            if project_id_result:
                project_id = project_id_result[0]
                root_idea = project_label.project.idea_map.root_idea

                self.cur.execute('''
                    INSERT INTO ideas (parent_id, project_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (0, project_id, root_idea.text_edit.text(), root_idea.tree_row, 0, root_idea.pos().x(), root_idea.pos().y()))

                parent_id = self.cur.lastrowid

                for j in range(len(root_idea.childs)):
                    self.save_idea(root_idea.childs[j], parent_id, project_id, j)

        self.con.commit()

    def save_idea(self, idea, parent_id, project_id, position):
        '''Метод для рекурсивного сохранения идей'''
        self.cur.execute('''
            INSERT INTO ideas (parent_id, project_id, text, tree_row, position, x_pos, y_pos) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (parent_id, project_id, idea.text_edit.text(), idea.tree_row, position, idea.pos().x(), idea.pos().y()))

        current_id = self.cur.lastrowid

        for i in range(len(idea.childs)):
            self.save_idea(idea.childs[i], current_id, project_id, i)

    def load_info(self):
        '''Загрузка данных из БД - теперь используем существующие методы main_window'''
        projects = self.cur.execute('''
            SELECT project, projectID FROM ProjectsList
        ''').fetchall()

        for project_name, project_id in projects:
            if hasattr(self.main_window, 'create_project_from_db'):
                new_project_label, new_project_window = self.main_window.create_project_from_db(
                    project_name)
                self.load_tasks(project_id, new_project_label)
                self.load_ideas(new_project_window, project_id)

    def load_tasks(self, project_id: int, project_label):
        '''Метод для загрузки задач'''
        tasks = self.cur.execute(
            '''SELECT task, isDone, deadline, isDefault, taskID FROM Tasks
            WHERE projectID = ? ORDER BY taskID''', (project_id,)).fetchall()

        for task_text, is_done, deadline_str, is_default, task_id in tasks:
            project_label.project.add_task(task_text, is_default)

            last_index = project_label.project.list_widget.count() - 1
            if last_index >= 0:
                task = project_label.project.list_widget.itemWidget(
                    project_label.project.list_widget.item(last_index))

                if is_done:
                    task.checkbox.setChecked(True)

                if deadline_str:
                    task.add_deadline_btn.setText(
                        f"До {deadline_str.replace('-', '.')}")
                    task.deadline = QtCore.QDate(int(deadline_str[:2]), int(
                        deadline_str[3:5]), int(deadline_str[6:]))
                    task.add_deadline_btn.blockSignals(True)

        project_label.get_project_status()

    def load_ideas(self, project, project_id: int):
        '''Загрузка идей'''
        root_data = self.cur.execute(
            '''SELECT text, x_pos, y_pos, id FROM ideas
            WHERE project_id = ? AND parent_id = 0''', (project_id,)
        ).fetchone()

        if root_data:
            root_text, root_x, root_y, root_id = root_data
            root_idea = project.idea_map.root_idea
            root_idea.text_edit.setText(root_text)
            root_idea.setPos(root_x, root_y)

            self._load_child_ideas(project, project_id, root_idea, root_id)

    def _load_child_ideas(self, project, project_id: int, parent_idea, parent_db_id: int):
        '''Рекурсивная загрузка дочерних идей'''
        child_ideas = self.cur.execute(
            '''SELECT text, x_pos, y_pos, tree_row, id FROM ideas
            WHERE project_id = ? AND parent_id = ?''', (project_id, parent_db_id)
        ).fetchall()

        for text, x_pos, y_pos, tree_row, idea_id in child_ideas:
            project.idea_map.add_idea(text, parent_idea)

            if parent_idea.childs:
                child_idea = parent_idea.childs[-1]
                child_idea.setPos(x_pos, y_pos)

                self._load_child_ideas(project, project_id, child_idea, idea_id)
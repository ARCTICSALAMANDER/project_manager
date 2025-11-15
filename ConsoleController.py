import subprocess
import os
import shutil
from datetime import datetime


class Console():
    def __init__(self, project_window):
        self.project_window = project_window
        self.commands = ['help', 'bind_folder', 'show_statistics']
        self.help_message = "PROJECT'S CONSOLE COMMANDS\nbind_folder <path to project's folder>: binds a folder to the project. After you bind a folder, this app will check for existing repository and the first commit.\n\n"
        self.help_message += "show_statistics: shows your activity stats including last completed task, closest deadline and completion percent.\n\n"
        self.help_message += "help: show this message again"
        self.git_manager = GitManager(project_window)

    def command_executer(self):
        '''Метод исполнения команд'''
        command = self.project_window.console_input.text()[2:]
        space_index = command.find(' ') if command.find(
            ' ') != -1 else len(command)
        if command[:space_index] == 'help':
            self.project_window.console_output.setPlainText(self.help_message)
        elif command[:space_index] == 'bind_folder':
            status = self.bind_folder(command, space_index)
            if not status:
                return
        elif command[:space_index] == 'show_statistics':
            self.show_statistics()
        else:
            self.project_window.console_output.setPlainText(
                f"SYNTAX ERROR:\nthere is no command '{command[:space_index]}'")

    def bind_folder(self, command: str, space_index: int) -> bool:
        '''Метод привязки папки через Git'''
        project_folder = command[space_index + 1:]
        status = self.git_manager.bind_git()
        if not status:
            self.project_window.console_output.setPlainText(
                f"ERROR:\nGit not found. Check if it had been added to PATH")

        status = self.git_manager.bind_folder(project_folder)
        folder_text = ""
        if status:
            self.project_window.console_output.setPlainText(
                "Folder binded successfully!")

            project_folder = project_folder.strip('"').strip("'")
            # не знаю, какой конкретно слэш будет в тексте пути, поэтому пробую оба варианта
            slash_index = project_folder.rfind('\\')
            if slash_index == -1:
                slash_index = project_folder.rfind('/')

            folder_text = './' + project_folder[slash_index + 1:]
            self.project_window.folder_path_label.setPlainText(
                f"Текущая папка проекта: {folder_text}")
            self.project_window.project_folder = project_folder

            if self.git_manager.is_repos:
                self.check_default_task(1, True)
                # проверяем, есть ли коммиты и отмечаем соответствующий чекбокс
                if self.git_manager.first_commit_check():
                    self.check_default_task(2, True)
                else:
                    self.check_default_task(2, False)
            else:
                self.check_default_task(1, False)

            return True
        else:
            return False

    def check_default_task(self, task_index, check: bool = True):
        '''Метод для отметки чекбоксов стандартных задач'''
        item = self.project_window.list_widget.item(task_index)
        if check:
            self.project_window.list_widget.itemWidget(
                item).checkbox.setChecked(True)
        else:
            self.project_window.list_widget.itemWidget(
                item).checkbox.setChecked(False)

    def show_statistics(self):
        '''Метод для показа статистики по проекту'''
        res = "THIS PROJECT STATS:\n"
        done_count = 0
        not_done_count = 0
        current_date = datetime.now().date()
        last_completed_task = None
        closest_deadline = None

        for i in range(self.project_window.list_widget.count()):
            item_widget = self.project_window.list_widget.itemWidget(
                self.project_window.list_widget.item(i))

            if item_widget.checkbox.isChecked():
                done_count += 1
            else:
                not_done_count += 1

            if item_widget.complete_time:
                if last_completed_task is None or item_widget.complete_time > last_completed_task.complete_time:
                    last_completed_task = item_widget

            if item_widget.deadline and not item_widget.checkbox.isChecked():
                # Преобразуем QDate в datetime.date для сравнения
                deadline_date = item_widget.deadline.toPyDate()

                # Проверяем, что дедлайн еще не прошел
                if deadline_date >= current_date:
                    if closest_deadline is None or deadline_date < closest_deadline.toPyDate():
                        closest_deadline = item_widget.deadline

        total_tasks = self.project_window.list_widget.count()
        completion_percentage = (
            done_count / total_tasks * 100) if total_tasks > 0 else 0

        res += f"{done_count} tasks done, {not_done_count} tasks left ({completion_percentage:.1f}% complete)\n"

        if last_completed_task:
            res += f"last completed task: {last_completed_task.task_name.text()}\n"
        else:
            res += "last completed task: none\n"

        if closest_deadline:
            res += f"closest deadline: {closest_deadline.toString('dd.MM.yy')}\n"
        else:
            res += "closest deadline: none\n"

        self.project_window.console_output.setPlainText(res)


class GitManager:
    '''Управляет операциями с Git'''

    def __init__(self, project_window):
        self.project_window = project_window
        self.git_path = ""
        self.project_folder = None
        self.is_repos = False
        self.has_commits = False

    def bind_git(self) -> bool:
        '''Привязка терминала Git через PATH'''
        git_path = shutil.which("git")
        if not git_path:
            return False
        else:
            self.git_path = git_path
            return True

    def bind_folder(self, project_folder: str) -> bool:
        '''Привязка папки. Вернет False в том случае, если папки не существует. Привяжет репозиторий, если он есть.'''
        project_folder = os.path.normpath(project_folder)
        if project_folder[0] == '"':  # убираем кавычки, если они есть
            project_folder = project_folder[1:]

        if project_folder[-1] == '"':
            project_folder = project_folder[:-1]

        self.is_repos = False
        self.has_commits = False

        status = self.repos_check(project_folder)
        if status:
            self.project_folder = project_folder
            return True
        else:
            return False

    def repos_check(self, project_folder) -> bool:
        '''Проверка на наличие репозитория в привязанной папке. Вернет True если существует папка и укажет self.is_repos = True,
        если есть репозиторий в ней, и False, если не существует папка'''
        self.is_repos = False

        status = subprocess.run(
            [self.git_path, '-C', project_folder, 'status'], capture_output=True, text=True)
        if status.returncode != 0:  # status будет равен 0 в том случае, если папка существует и в ней есть репозиторий
            error_text = status.stderr.lower()  # смотрим текст ошибки
            if "not a git repository" in error_text:  # если папка есть, но в ней нет репозитория
                self.project_window.console_output.setPlainText(
                    "Folder binded successfully!")
                return True
            else:  # если папки вообще нет
                self.project_window.console_output.setPlainText(
                    f"FOLDER BINDING ERROR:\n{error_text}")
                return False
        else:
            self.project_window.console_output.setPlainText(
                "Folder binded successfully, repository detected!")
            self.is_repos = True
            return True

    def first_commit_check(self) -> bool:
        '''Метод проверки на наличие коммитов. Вернет True, если коммиты есть,
        и False, если нет'''
        if self.project_folder:
            commit_status = subprocess.run(
                [self.git_path, '-C', self.project_folder, 'rev-list', '-n', '1', '--all'], capture_output=True, text=True)

            if commit_status.returncode == 0 and commit_status.stdout.strip():  # команда выполнилась успешно и есть вывод
                return True
            else:
                return False
        else:
            return False
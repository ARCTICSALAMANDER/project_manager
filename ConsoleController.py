import subprocess
import os
import shutil
from datetime import datetime


class Console():
    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        self.commands = ['help', 'bind_folder', 'show_statistics']
        self.helpMessage = "PROJECT'S CONSOLE COMMANDS\nbind_folder <path to project's folder>: binds a folder to the project. After you bind a folder, this app will check for existing repository and the first commit.\nshow_statistics: shows your activity stats including last completed task, closest deadline and completion percent."
        self.gitManager = GitManager(projectWindow)

    def commandExecuter(self):
        '''Метод исполнения команд'''
        command = self.projectWindow.consoleInput.text()[2:]
        space_index = command.find(' ') if command.find(
            ' ') != -1 else len(command)
        if command[:space_index] == 'help':
            self.projectWindow.consoleOutput.setPlainText(self.helpMessage)
        elif command[:space_index] == 'bind_folder':
            status = self.bindFolder(command, space_index)
            if not status:
                return
        elif command[:space_index] == 'show_statistics':
            self.show_statistics()
        else:
            self.projectWindow.consoleOutput.setPlainText(
                f"SYNTAX ERROR:\nthere is no command '{command[:space_index]}'")

    def bindFolder(self, command: str, space_index: int) -> bool:
        '''Метод привязки папки через Git'''
        projectFolder = command[space_index + 1:]
        status = self.gitManager.bindGit()
        if not status:
            self.projectWindow.consoleOutput.setPlainText(
                f"ERROR:\nGit not found. Check if it had been added to PATH")

        status = self.gitManager.bindFolder(projectFolder)
        folderText = ""
        if status:
            self.projectWindow.consoleOutput.setPlainText(
                "Folder binded successfully!")

            projectFolder = projectFolder.strip('"').strip("'")
            # не знаю, какой конкретно слэш будет в тексте пути, поэтому пробую оба варианта
            slashIndex = projectFolder.rfind('\\')
            if slashIndex == -1:
                slashIndex = projectFolder.rfind('/')

            folderText = './' + projectFolder[slashIndex + 1:]
            self.projectWindow.folderPathLabel.setPlainText(
                f"Текущая папка проекта: {folderText}")
            self.projectWindow.projectFolder = projectFolder

            if self.gitManager.isRepos:
                self.checkDefaultTask(1, True)
                # проверяем, есть ли коммиты и отмечаем соответствующий чекбокс
                if self.gitManager.firstCommitCheck():
                    self.checkDefaultTask(2, True)
                else:
                    self.checkDefaultTask(2, False)
            else:
                self.checkDefaultTask(1, False)

            return True
        else:
            return False

    def checkDefaultTask(self, taskIndex, check: bool = True):
        '''Метод для отметки чекбоксов стандартных задач'''
        item = self.projectWindow.listWidget.item(taskIndex)
        if check:
            self.projectWindow.listWidget.itemWidget(
                item).checkbox.setChecked(True)
        else:
            self.projectWindow.listWidget.itemWidget(
                item).checkbox.setChecked(False)

    def show_statistics(self):
        '''Метод для показа статистики по проекту'''
        res = "THIS PROJECT STATS:\n"
        doneCount = 0
        notDoneCount = 0
        current_date = datetime.now().date()
        lastCompletedTask = None
        closestDeadline = None

        for i in range(self.projectWindow.listWidget.count()):
            item_widget = self.projectWindow.listWidget.itemWidget(
                self.projectWindow.listWidget.item(i))

            if item_widget.checkbox.isChecked():
                doneCount += 1
            else:
                notDoneCount += 1

            if item_widget.completeTime:
                if lastCompletedTask is None or item_widget.completeTime > lastCompletedTask.completeTime:
                    lastCompletedTask = item_widget

            if item_widget.deadline and not item_widget.checkbox.isChecked():
                # Преобразуем QDate в datetime.date для сравнения
                deadline_date = item_widget.deadline.toPyDate()

                # Проверяем, что дедлайн еще не прошел
                if deadline_date >= current_date:
                    if closestDeadline is None or deadline_date < closestDeadline.toPyDate():
                        closestDeadline = item_widget.deadline

        total_tasks = self.projectWindow.listWidget.count()
        completion_percentage = (
            doneCount / total_tasks * 100) if total_tasks > 0 else 0

        res += f"{doneCount} tasks done, {notDoneCount} tasks left ({completion_percentage:.1f}% complete)\n"

        if lastCompletedTask:
            res += f"last completed task: {lastCompletedTask.taskName.text()}\n"
        else:
            res += "last completed task: none\n"

        if closestDeadline:
            res += f"closest deadline: {closestDeadline.toString('dd.MM.yy')}\n"
        else:
            res += "closest deadline: none\n"

        self.projectWindow.consoleOutput.setPlainText(res)


class GitManager:
    '''Управляет операциями с Git'''

    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        self.gitPath = ""
        self.projectFolder = None
        self.isRepos = False
        self.hasCommits = False

    def bindGit(self) -> bool:
        '''Привязка терминала Git через PATH.'''
        gitPath = shutil.which("git")
        if not gitPath:
            return False
        else:
            self.gitPath = gitPath
            return True

    def bindFolder(self, projectFolder: str) -> bool:
        '''Привязка папки. Вернет False  в том случае, если папки не существует. Привяжет репозиторий, если он есть.'''
        projectFolder = os.path.normpath(projectFolder)
        if projectFolder[0] == '"':  # убираем кавычки, если они есть
            projectFolder = projectFolder[1:]

        if projectFolder[-1] == '"':
            projectFolder = projectFolder[:-1]

        self.isRepos = False
        self.hasCommits = False

        status = self.reposCheck(projectFolder)
        if status:
            self.projectFolder = projectFolder
            return True
        else:
            return False

    def reposCheck(self, projectFolder) -> bool:
        '''Проверка на наличие репозитория в привязанной папке. Вернет True если существует папка и укажет self.isRepos = True,
        если есть репозиторий в ней, и False, если не существует папка'''
        self.isRepos = False

        status = subprocess.run(
            [self.gitPath, '-C', projectFolder, 'status'], capture_output=True, text=True)
        if status.returncode != 0:  # status будет равен 0 в том случае, если папка существует и в ней есть репозиторий
            errorText = status.stderr.lower()  # смотрим текст ошибки
            if "not a git repository" in errorText:  # если папка есть, но в ней нет репозитория
                self.projectWindow.consoleOutput.setPlainText(
                    "Folder binded successfully!")
                return True
            else:  # если папки вообще нет
                self.projectWindow.consoleOutput.setPlainText(
                    f"FOLDER BINDING ERROR:\n{errorText}")
                return False
        else:
            self.projectWindow.consoleOutput.setPlainText(
                "Folder binded successfully, repository detected!")
            self.isRepos = True
            return True

    def firstCommitCheck(self) -> bool:
        '''Метод проверки на наличие коммитов. Вернет True, если коммиты есть,
        и False, если нет'''
        if self.projectFolder:
            commitStatus = subprocess.run(
                [self.gitPath, '-C', self.projectFolder, 'rev-list', '-n', '1', '--all'], capture_output=True, text=True)

            if commitStatus.returncode == 0 and commitStatus.stdout.strip():  # команда выполнилась успешно и есть вывод
                return True
            else:
                return False
        else:
            return False

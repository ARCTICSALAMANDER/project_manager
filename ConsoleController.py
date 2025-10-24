import subprocess, os, shutil


class Console():
    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        self.commands = ['help', 'add_task', 'delete_task']
        self.helpMessage = "PROJECT'S CONSOLE COMMANDS\nadd_task <task name>: adds a task to the task list\ndelete_task <task number>: deletes a task from the task list. Tasks' numeration starts from the top"
        self.gitManager = GitManager(projectWindow)

    def commandExecuter(self):
        command = self.projectWindow.consoleInput.text()[2:]
        space_index = command.find(' ') if command.find(' ') != -1 else len(command)
        if command[:space_index] == 'help':
            self.projectWindow.consoleOutput.setPlainText(self.helpMessage)
        elif command[:space_index] == 'add_task':
            taskName = command[space_index + 1:]
            self.projectWindow.addTask(taskName)
            self.projectWindow.consoleOutput.setPlainText(f"Successfully added '{taskName}' to the task list")
        elif command[:space_index] == 'delete_task':
            try:
                taskNumber = int(command[space_index + 1:])
                if taskNumber < 1:
                    self.projectWindow.consoleOutput.setPlainText(f"INVALID ARGUMENT ERROR: \ntask's number cannot be less than 1")
                    return
            except ValueError:
                self.projectWindow.consoleOutput.setPlainText(f"INVALID ARGUMENT ERROR: \n{taskNumber} cannot be a argument. Please, check existence of a task with this number and if this argument is a integer")
                return
            itemCheck = self.projectWindow.deleteTask(int(taskNumber))
            if not itemCheck:
                self.projectWindow.consoleOutput.setPlainText(f"INVALID ARGUMENT ERROR:\nThere is no task with number {taskNumber}")
            else:
                self.projectWindow.consoleOutput.setPlainText(f"Successfully deleted task №{taskNumber} from the task list")
        elif command[:space_index] == 'bind_folder':
            status = self.bindFolder(command, space_index)
            if not status:
                return
        else:
            self.projectWindow.consoleOutput.setPlainText(f"SYNTAX ERROR:\nthere is no command '{command[:space_index]}'")

    def bindFolder(self, command: str, space_index: int) -> bool:
        '''Метод привязки папки через Git'''
        projectFolderPath = command[space_index + 1:]
        status = self.gitManager.bindGit()
        if not status:
            self.projectWindow.consoleOutput.setPlainText(f"ERROR:\nGit not found. Check if it had been added to PATH")
        
        status = self.gitManager.bindFolder(projectFolderPath)
        if status:
            self.projectWindow.consoleOutput.setPlainText("Folder binded successfully!")
            return True
        else:
            return False

class GitManager:
    '''Управляет операциями с Git'''
    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        self.gitPath = ""
        self.projectFolder = None
        self.isRepos = False

    def bindGit(self) -> bool:
        '''Привязка терминала Git через PATH.'''
        gitPath = shutil.which("git")
        if not gitPath:
            return False
        else:
            self.gitPath = gitPath
            return True

    def bindFolder(self, folderPath: str) -> bool:
        '''Привязка папки. Вернет False  в том случае, если папки не существует. Привяжет репозиторий, если он есть.'''
        folderPath = os.path.normpath(folderPath)
        if folderPath[0] == '"': # убираем кавычки, если они есть
            folderPath = folderPath[1:]

        if folderPath[-1] == '"':
            folderPath = folderPath[:-1]

        status = subprocess.run([self.gitPath, '-C', folderPath, 'status'], capture_output=True, text=True)
        if status.returncode != 0: # status будет равен 0 в том случае, если папка существует и в ней есть репозиторий
            errorText = status.stderr.lower() # смотрим текст ошибки
            if "not a git repository" in errorText: # если папка есть, но в ней нет репозитория
                self.projectWindow.consoleOutput.setPlainText("Folder binded successfully!")
                return True
            else: # если папки вообще нет
                self.projectWindow.consoleOutput.setPlainText(f"FOLDER BINDING ERROR:\n{errorText}")
                return False
        else:
            self.isRepos = True
            return True
        

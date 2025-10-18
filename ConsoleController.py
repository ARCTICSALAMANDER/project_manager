class Console():
    def __init__(self, projectWindow):
        self.projectWindow = projectWindow
        self.commands = ['help', 'add_task', 'delete_task']
        self.helpMessage = "PROJECT'S CONSOLE COMMANDS\nadd_task <task name>: adds a task to the task list\ndelete_task <task number>: deletes a task from the task list. Tasks' numeration starts from the top"

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
            self.projectWindow.deleteTask(int(taskNumber))
            self.projectWindow.consoleOutput.setPlainText(f"Successfully deleted '{taskNumber}' from the task list")
        else:
            self.projectWindow.consoleOutput.setPlainText(f"SYNTAX ERROR: \nthere is no command '{command[:space_index]}'")


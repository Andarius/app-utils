from rich.console import Console


class ConsoleLog:
    WARNING = '[[bold orange]WARNING[/]]'
    INFO = '[[bold green]INFO[/]]'
    ERROR = '[[bold red]ERROR[/]]'

    def __init__(self):
        self.console = Console()

    def info(self, *args):
        self.console.log(ConsoleLog.INFO, *args)

    def warn(self, *args):
        self.console.log(ConsoleLog.WARNING, *args)

    def error(self, *args):
        self.console.log(ConsoleLog.ERROR, *args)


CONSOLE = ConsoleLog()

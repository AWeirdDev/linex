from datetime import datetime

from rich.console import Console

console = Console()

class TimeGenerator:
    def __repr__(self) -> str:
        return f"{datetime.now():%H:%M:%S}"

time = TimeGenerator()

class logger:
    """Represents a simple logger."""

    disabled = False

    @staticmethod
    def print(*args, **kwargs):
        if logger.disabled:
            return

        """Shortcut for ``console.print``."""
        console.print(*args, **kwargs)

    @staticmethod
    def print_exception():
        """Prints exceptions."""
        console.print_exception()

    @staticmethod
    def log(content: str) -> None:
        """Logs any content to the console with a timestamp.

        Args:
            content (str): The content to log.
        """
        if logger.disabled:
            return

        console.print(
            f'[white d]{time}[/white d] ' + content.replace('\n', f'\n{" " * 9}')
        )

    class routing:
        @staticmethod
        def ok(method: str, route: str, message: str):
            """Logs a valid / successful HTTP request to a console.

            Args:
                method (str): The request method.
                route (str): The route. (e.g., ``/some/route``)
                message (str): Any message.
            """
            if logger.disabled:
                return

            logger.log(
                f"[green]{method}[/green] {route} - {message}"
            )

        @staticmethod
        def fail(method: str, route: str, message: str):
            """Logs a invalid / failing HTTP request to a console.

            Args:
                method (str): The request method.
                route (str): The route. (e.g., ``/some/route``)
                message (str): Message indicating the failure.
            """
            if logger.disabled:
                return

            logger.log(
                f"[red]{method}[/red] {route} - {message}"
            )

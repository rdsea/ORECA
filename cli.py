import sys

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from deployments.applications.application_manager import ApplicationManager

logger.remove()
logger.add(sys.stderr, level="INFO")

application_manager = ApplicationManager()
console = Console()

commands = ["init_telemetry", "destroy", "set_log_level", "exit"]
command_completer = WordCompleter(commands, ignore_case=True)


def set_log_level():
    valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    level = Prompt.ask("Enter new log level", choices=valid_levels, default="INFO")
    logger.remove()
    logger.add(sys.stderr, level=level)
    console.print(f"[bold blue]✔ Log level set to {level}[/bold blue]")


def main():
    session = PromptSession()
    console.print(
        Panel(
            "[bold green]Telemetry CLI[/bold green]\nType a command: [cyan]init_telemetry[/cyan], [cyan]destroy[/cyan], [cyan]set_log_level[/cyan], or [cyan]exit[/cyan].",
            title="Welcome",
        )
    )

    while True:
        try:
            user_input = (
                session.prompt("> ", completer=command_completer).strip().lower()
            )

            if user_input == "init_telemetry":
                application_manager.init_telemetry()
                console.print("[bold green]✔  Telemetry initialized[/bold green]")

            elif user_input == "destroy":
                application_manager.destroy()
                console.print("[bold green]✔  Telemetry destroyed[/bold green]")

            elif user_input == "set_log_level":
                set_log_level()

            elif user_input == "exit":
                console.print("[yellow]👋 Exiting the CLI. Goodbye![/yellow]")
                break

            else:
                console.print(
                    f"[bold red]Unknown command:[/bold red] [italic]{user_input}[/italic]"
                )

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Ctrl+C or EOF detected. Exiting...[/dim]")
            break


if __name__ == "__main__":
    main()

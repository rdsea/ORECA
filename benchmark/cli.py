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

commands = [
    "init_telemetry",
    "destroy",
    "set_log_level",
    "exit",
    "init_metric",
    "init_log",
    "init_trace",
    "destroy_metric",
    "destroy_log",
    "destroy_trace",
    "init_visualization",
    "destroy_visualization",
]
command_completer = WordCompleter(commands, ignore_case=True)


def set_log_level():
    valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    level = Prompt.ask("Enter new log level", choices=valid_levels, default="INFO")
    logger.remove()
    logger.add(sys.stderr, level=level)
    console.print(f"[bold blue]✔ Log level set to {level}[/bold blue]")


def show_welcome_panel():
    command_list = ", ".join(f"[cyan]{cmd}[/cyan]" for cmd in commands)
    panel_text = (
        "[bold green]Telemetry CLI[/bold green]\nType a command: " + command_list + "."
    )
    console.print(Panel(panel_text, title="Welcome"))


def main():
    session = PromptSession()
    show_welcome_panel()

    while True:
        try:
            user_input = (
                session.prompt("> ", completer=command_completer).strip().lower()
            )

            match user_input:
                case "init_telemetry":
                    application_manager.init_telemetry()
                    console.print("[bold green]✔  Telemetry initialized[/bold green]")

                case "destroy":
                    application_manager.destroy()
                    console.print("[bold green]✔  Telemetry destroyed[/bold green]")

                case "init_metric":
                    application_manager.init_metric()
                    console.print("[bold green]✔  Metric initialized[/bold green]")

                case "init_log":
                    application_manager.init_log()
                    console.print("[bold green]✔  Log initialized[/bold green]")

                case "init_visualization":
                    application_manager.init_visualization()
                    console.print(
                        "[bold green]✔  Visualization initialized[/bold green]"
                    )

                case "init_trace":
                    application_manager.init_trace()
                    console.print("[bold green]✔  Trace initialized[/bold green]")

                case "destroy_metric":
                    application_manager.destroy_metric()
                    console.print("[bold green]✔  Metric destroyed[/bold green]")

                case "destroy_log":
                    application_manager.destroy_log()
                    console.print("[bold green]✔  Log destroyed[/bold green]")

                case "destroy_visualization":
                    application_manager.destroy_visualization()
                    console.print("[bold green]✔  Visualization destroyed[/bold green]")

                case "destroy_trace":
                    application_manager.destroy_trace()
                    console.print("[bold green]✔  Trace destroyed[/bold green]")

                case "set_log_level":
                    set_log_level()

                case "exit":
                    console.print("[yellow]👋 Exiting the CLI. Goodbye![/yellow]")
                    break

                case _:
                    console.print(
                        f"[bold red]Unknown command:[/bold red] [italic]{user_input}[/italic]"
                    )

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Ctrl+C or EOF detected. Exiting...[/dim]")
            break


if __name__ == "__main__":
    main()

# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import click
import typer
from rich import print
from rich.table import Table
from typing_extensions import Annotated

from primaite import _PRIMAITE_ROOT, PRIMAITE_CONFIG
from primaite.simulator import LogLevel
from primaite.utils.cli.primaite_config_utils import is_dev_mode, update_primaite_application_config

dev = typer.Typer()

PRODUCTION_MODE_MESSAGE = (
    "\n[green]:rocket::rocket::rocket: "
    " PrimAITE is running in Production mode "
    " :rocket::rocket::rocket: [/green]\n"
)

DEVELOPER_MODE_MESSAGE = (
    "\n[yellow] :construction::construction::construction: "
    " PrimAITE is running in Development mode "
    " :construction::construction::construction: [/yellow]\n"
)


def dev_mode():
    """
    CLI commands relevant to the dev-mode for PrimAITE.

    The dev-mode contains tools that help with the ease of developing or debugging PrimAITE.

    By default, PrimAITE will be in production mode.

    To enable development mode, use `primaite dev-mode enable`
    """


@dev.command()
def show():
    """Show if PrimAITE is in development mode or production mode."""
    # print if dev mode is enabled
    print(DEVELOPER_MODE_MESSAGE if is_dev_mode() else PRODUCTION_MODE_MESSAGE)

    table = Table(title="Current Dev-Mode Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="default")
    for setting, value in PRIMAITE_CONFIG["developer_mode"].items():
        table.add_row(setting, str(value))

    print(table)
    print("\nTo see available options, use [cyan]`primaite dev-mode --help`[/cyan]\n")


@dev.command()
def enable():
    """Enable the development mode for PrimAITE."""
    # enable dev mode
    PRIMAITE_CONFIG["developer_mode"]["enabled"] = True
    update_primaite_application_config()
    print(DEVELOPER_MODE_MESSAGE)


@dev.command()
def disable():
    """Disable the development mode for PrimAITE."""
    # disable dev mode
    PRIMAITE_CONFIG["developer_mode"]["enabled"] = False
    update_primaite_application_config()
    print(PRODUCTION_MODE_MESSAGE)


def config_callback(
    ctx: typer.Context,
    sys_log_level: Annotated[
        LogLevel,
        typer.Option(
            "--sys-log-level",
            "-level",
            click_type=click.Choice(LogLevel._member_names_, case_sensitive=False),
            help="The level of system logs to output.",
            show_default=False,
        ),
    ] = None,
    output_sys_logs: Annotated[
        bool,
        typer.Option(
            "--output-sys-logs/--no-sys-logs", "-sys/-nsys", help="Output system logs to file.", show_default=False
        ),
    ] = None,
    output_pcap_logs: Annotated[
        bool,
        typer.Option(
            "--output-pcap-logs/--no-pcap-logs",
            "-pcap/-npcap",
            help="Output network packet capture logs to file.",
            show_default=False,
        ),
    ] = None,
    output_to_terminal: Annotated[
        bool,
        typer.Option(
            "--output-to-terminal/--no-terminal", "-t/-nt", help="Output system logs to terminal.", show_default=False
        ),
    ] = None,
):
    """Configure the development tools and environment."""
    if ctx.params.get("sys_log_level") is not None:
        PRIMAITE_CONFIG["developer_mode"]["sys_log_level"] = ctx.params.get("sys_log_level")
        print(f"PrimAITE dev-mode config updated sys_log_level={ctx.params.get('sys_log_level')}")

    if output_sys_logs is not None:
        PRIMAITE_CONFIG["developer_mode"]["output_sys_logs"] = output_sys_logs
        print(f"PrimAITE dev-mode config updated {output_sys_logs=}")

    if output_pcap_logs is not None:
        PRIMAITE_CONFIG["developer_mode"]["output_pcap_logs"] = output_pcap_logs
        print(f"PrimAITE dev-mode config updated {output_pcap_logs=}")

    if output_to_terminal is not None:
        PRIMAITE_CONFIG["developer_mode"]["output_to_terminal"] = output_to_terminal
        print(f"PrimAITE dev-mode config updated {output_to_terminal=}")

    # update application config
    update_primaite_application_config()


config_typer = typer.Typer(
    callback=config_callback,
    name="config",
    no_args_is_help=True,
    invoke_without_command=True,
)
dev.add_typer(config_typer)


@config_typer.command()
def path(
    directory: Annotated[
        str,
        typer.Argument(
            help="Directory where the system logs and PCAP logs will be output. By default, this will be where the"
            "root of the PrimAITE repository is located.",
            show_default=False,
        ),
    ] = None,
    default: Annotated[
        bool,
        typer.Option(
            "--default",
            "-root",
            help="Set PrimAITE to output system logs and pcap logs to the PrimAITE repository root.",
        ),
    ] = None,
):
    """Set the output directory for the PrimAITE system and PCAP logs."""
    if default:
        PRIMAITE_CONFIG["developer_mode"]["output_dir"] = None
        # update application config
        update_primaite_application_config()
        print(
            f"PrimAITE dev-mode output_dir [cyan]"
            f"{str(_PRIMAITE_ROOT.parent.parent / 'simulation_output')}"
            f"[/cyan]"
        )
        return

    if directory:
        PRIMAITE_CONFIG["developer_mode"]["output_dir"] = directory
        # update application config
        update_primaite_application_config()
        print(f"PrimAITE dev-mode output_dir [cyan]{directory}[/cyan]")

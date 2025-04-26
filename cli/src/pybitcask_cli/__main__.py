"""Command-line interface for the Bitcask key-value store.

This module provides a CLI for interacting with the Bitcask key-value store,
including operations like put, get, delete, and mode switching.
"""

import atexit
import json
import subprocess
import sys
from os.path import abspath, dirname
from pathlib import Path
from typing import Optional

import click

from pybitcask.bitcask import Bitcask
from pybitcask.rotation import (
    CompositeRotation,
    EntryCountRotation,
    SizeBasedRotation,
    TimeBasedRotation,
)

# Add the project root to Python path
project_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.append(project_root)


class BitcaskCLI:
    """Command-line interface for the Bitcask key-value store.

    This class provides methods for interacting with the Bitcask database
    through a command-line interface, including data operations and mode switching.
    """

    def __init__(
        self,
        data_dir: str = "./data",
        debug_mode: bool = False,
        max_file_size: Optional[int] = None,
        max_entries: Optional[int] = None,
        rotation_interval: Optional[int] = None,
    ):
        """Initialize the Bitcask CLI.

        Args:
        ----
            data_dir: Directory where the database files will be stored
            debug_mode: Whether to run in debug mode (human-readable format)
            max_file_size: Maximum file size in bytes before rotation
            max_entries: Maximum number of entries before rotation
            rotation_interval: Time interval in seconds between rotations

        """
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "config.json"
        self.db = None

        # Load config if exists, otherwise use default
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)
                self.debug_mode = config.get("debug_mode", debug_mode)
                config_max_file_size = config.get("max_file_size")
                config_max_entries = config.get("max_entries")
                config_rotation_interval = config.get("rotation_interval")
        else:
            self.debug_mode = debug_mode
            config_max_file_size = max_file_size
            config_max_entries = max_entries
            config_rotation_interval = rotation_interval
            self._save_config()

        # Create rotation strategy if any rotation parameters are set
        rotation_strategies = []
        if config_max_file_size is not None:
            rotation_strategies.append(SizeBasedRotation(config_max_file_size))
        if config_max_entries is not None:
            rotation_strategies.append(EntryCountRotation(config_max_entries))
        if config_rotation_interval is not None:
            rotation_strategies.append(TimeBasedRotation(config_rotation_interval))

        self.rotation_strategy = (
            CompositeRotation(rotation_strategies) if rotation_strategies else None
        )

    def _save_config(self) -> None:
        """Save the current configuration to file.

        This method writes the current settings to the config file.
        """
        max_file_size = None
        max_entries = None
        rotation_interval = None

        if isinstance(self.rotation_strategy, CompositeRotation):
            for strategy in self.rotation_strategy.strategies:
                if isinstance(strategy, SizeBasedRotation):
                    max_file_size = strategy.max_size_bytes
                elif isinstance(strategy, EntryCountRotation):
                    max_entries = strategy.max_entries
                elif isinstance(strategy, TimeBasedRotation):
                    rotation_interval = strategy.interval_seconds

        config = {
            "debug_mode": self.debug_mode,
            "max_file_size": max_file_size,
            "max_entries": max_entries,
            "rotation_interval": rotation_interval,
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def ensure_db(self) -> None:
        """Ensure the database connection is established.

        If the database is not connected, this method creates a new connection
        and registers the cleanup handler.
        """
        if self.db is None:
            self.db = Bitcask(
                self.data_dir,
                debug_mode=self.debug_mode,
                rotation_strategy=self.rotation_strategy,
            )
            atexit.register(self.close)

    def get_current_mode(self) -> str:
        """Get the current mode as a string."""
        return "debug" if self.debug_mode else "normal"

    def show_mode(self) -> None:
        """Show the current mode."""
        mode = self.get_current_mode()
        click.echo(click.style(f"Current mode: {mode}", fg="blue"))

    def put(self, key: str, value: str) -> None:
        """Store a value in the database."""
        try:
            self.ensure_db()
            self.db.put(key, value)
            click.echo(
                click.style(f"✓ Successfully stored value for key: {key}", fg="green")
            )
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def get(self, key: str) -> None:
        """Retrieve a value from the database."""
        try:
            self.ensure_db()
            value = self.db.get(key)
            if value is None:
                click.echo(click.style(f"✗ Key '{key}' not found", fg="yellow"))
                return
            click.echo(click.style(f"Value for key '{key}':", fg="blue"))
            click.echo(value)
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def delete(self, key: str) -> None:
        """Delete a value from the database."""
        try:
            self.ensure_db()
            if self.db.delete(key):
                click.echo(
                    click.style(f"✓ Successfully deleted key: {key}", fg="green")
                )
            else:
                click.echo(click.style(f"✗ Key '{key}' not found", fg="yellow"))
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def list(self) -> None:
        """List all keys in the database."""
        try:
            self.ensure_db()
            keys = self.db.list_keys()
            if not keys:
                click.echo(click.style("No keys found", fg="yellow"))
                return
            click.echo(click.style("Available keys:", fg="blue"))
            for key in keys:
                click.echo(f"  • {key}")
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def start_server(self, port: int = 8000) -> None:
        """Start the Bitcask server."""
        try:
            click.echo(
                click.style(f"Starting Bitcask server on port {port}...", fg="blue")
            )
            self.server_process = subprocess.Popen(
                ["python", "server.py", "--port", str(port)],
                cwd=dirname(dirname(abspath(__file__))),
            )
            atexit.register(self.stop_server)
            self.server_url = f"http://localhost:{port}"
            click.echo(click.style("✓ Server started successfully", fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Error starting server: {e}", fg="red"), err=True)

    def stop_server(self) -> None:
        """Stop the Bitcask server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.server_url = None

    def close(self):
        """Close the database connection."""
        if self.db is not None:
            self.db.close()
            self.db = None

    def clear(self) -> None:
        """Clear all data from the database."""
        try:
            self.ensure_db()
            self.db.clear()
            click.echo(click.style("✓ Database cleared successfully", fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def switch_mode(self, debug_mode: bool) -> None:
        """Switch between debug and normal modes.

        This will:
        1. Close and clear the database
        2. Delete all data files
        3. Clear the data directory
        4. Switch to the new mode
        5. Create a new empty database in the new mode
        """
        try:
            # Show warning and get confirmation
            mode = "debug" if debug_mode else "normal"
            click.echo(
                click.style(
                    "⚠️ WARNING: Switching modes will delete ALL data!",
                    fg="yellow",
                    bold=True,
                )
            )
            click.echo(click.style("This action cannot be undone.", fg="yellow"))
            if not click.confirm(
                click.style(f"Do you want to switch to {mode} mode?", fg="yellow")
            ):
                click.echo(click.style("Mode switch cancelled", fg="blue"))
                return

            # Close and clear the database
            if self.db is not None:
                self.db.close()
                self.db = None

            # Delete all data files and clear the directory
            if self.data_dir.exists():
                for file in self.data_dir.glob("*"):
                    if (
                        file.is_file() and file.name != "config.json"
                    ):  # Don't delete config file
                        file.unlink()
                # Recreate the directory if it was deleted
                self.data_dir.mkdir(exist_ok=True)

            # Switch mode and create new database
            self.debug_mode = debug_mode
            self._save_config()  # Save the new mode
            self.db = Bitcask(self.data_dir, debug_mode=self.debug_mode)

            click.echo(click.style(f"✓ Switched to {mode} mode", fg="green"))
            click.echo(click.style("✓ Database cleared completely", fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@click.group()
@click.option("--data-dir", default="./data", help="Data directory path")
@click.option("--debug", is_flag=True, help="Run in debug mode (human-readable format)")
@click.option(
    "--max-file-size",
    type=int,
    help="Maximum file size in bytes before rotation",
)
@click.option(
    "--max-entries",
    type=int,
    help="Maximum number of entries before rotation",
)
@click.option(
    "--rotation-interval",
    type=int,
    help="Time interval in seconds between rotations",
)
@click.pass_context
def cli(ctx, data_dir, debug, max_file_size, max_entries, rotation_interval):
    """Bitcask CLI - A command-line interface for the Bitcask key-value store."""
    ctx.obj = BitcaskCLI(
        data_dir,
        debug_mode=debug,
        max_file_size=max_file_size,
        max_entries=max_entries,
        rotation_interval=rotation_interval,
    )


@cli.command()
@click.argument("key")
@click.argument("value")
@click.pass_obj
def put(cli: BitcaskCLI, key: str, value: str):
    """Store a value in the database."""
    cli.put(key, value)


@cli.command()
@click.argument("key")
@click.pass_obj
def get(cli: BitcaskCLI, key: str):
    """Retrieve a value from the database."""
    cli.get(key)


@cli.command()
@click.argument("key")
@click.pass_obj
def delete(cli: BitcaskCLI, key: str):
    """Delete a value from the database."""
    cli.delete(key)


@cli.command()
@click.pass_obj
def list(cli: BitcaskCLI):
    """List all keys in the database."""
    cli.list()


@cli.command()
@click.pass_obj
def clear(cli: BitcaskCLI):
    """Clear all data from the database."""
    cli.clear()


@cli.group()
def mode():
    """Switch between debug and normal modes."""
    pass


@mode.command()
@click.pass_obj
def debug(cli: BitcaskCLI):
    """Switch to debug mode (human-readable format)."""
    cli.switch_mode(debug_mode=True)


@mode.command()
@click.pass_obj
def normal(cli: BitcaskCLI):
    """Switch to normal mode (binary format)."""
    cli.switch_mode(debug_mode=False)


@mode.command()
@click.pass_obj
def show(cli: BitcaskCLI):
    """Show the current mode."""
    cli.show_mode()


@cli.group()
def config():
    """Manage database configuration settings."""
    pass


@config.command()
@click.option(
    "--max-file-size",
    type=int,
    help="Maximum file size in bytes before rotation",
)
@click.option(
    "--max-entries",
    type=int,
    help="Maximum number of entries before rotation",
)
@click.option(
    "--rotation-interval",
    type=int,
    help="Time interval in seconds between rotations",
)
@click.pass_obj
def set(cli: BitcaskCLI, max_file_size, max_entries, rotation_interval):
    """Set rotation configuration parameters."""
    try:
        # Create rotation strategy if any rotation parameters are set
        rotation_strategies = []
        if max_file_size is not None:
            rotation_strategies.append(SizeBasedRotation(max_file_size))
        if max_entries is not None:
            rotation_strategies.append(EntryCountRotation(max_entries))
        if rotation_interval is not None:
            rotation_strategies.append(TimeBasedRotation(rotation_interval))

        cli.rotation_strategy = (
            CompositeRotation(rotation_strategies) if rotation_strategies else None
        )

        # Ensure the database is using the new rotation strategy
        if cli.db is not None:
            cli.db.rotation_strategy = cli.rotation_strategy

        cli._save_config()
        click.echo(click.style("✓ Configuration updated successfully", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@config.command()
@click.pass_obj
def view(cli: BitcaskCLI):
    """Show current configuration settings."""
    try:
        max_file_size = None
        max_entries = None
        rotation_interval = None

        if isinstance(cli.rotation_strategy, CompositeRotation):
            for strategy in cli.rotation_strategy.strategies:
                if isinstance(strategy, SizeBasedRotation):
                    max_file_size = strategy.max_size_bytes
                elif isinstance(strategy, EntryCountRotation):
                    max_entries = strategy.max_entries
                elif isinstance(strategy, TimeBasedRotation):
                    rotation_interval = strategy.interval_seconds

        config = {
            "debug_mode": cli.debug_mode,
            "max_file_size": max_file_size,
            "max_entries": max_entries,
            "rotation_interval": rotation_interval,
        }
        click.echo(click.style("Current configuration:", fg="blue"))
        for key, value in config.items():
            click.echo(f"{key}: {value}")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@config.command()
@click.pass_obj
def reset(cli: BitcaskCLI):
    """Reset all configuration settings to defaults."""
    try:
        cli.rotation_strategy = None
        cli._save_config()
        click.echo(click.style("✓ Configuration reset to defaults", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


if __name__ == "__main__":
    cli()

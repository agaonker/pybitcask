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
import pkg_resources

from pybitcask.bitcask import Bitcask
from pybitcask.config import config as bitcask_config

# Add the project root to Python path
project_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.append(project_root)

# Version compatibility check
try:
    cli_version = pkg_resources.get_distribution("pybitcask-cli").version
    core_version = pkg_resources.get_distribution("pybitcask").version
    if cli_version != core_version:
        click.echo(
            click.style(
                "Warning: CLI version ({}) differs from core version ({})".format(
                    cli_version, core_version
                ),
                fg="yellow",
            )
        )
except pkg_resources.DistributionNotFound:
    pass  # Skip version check if not installed as package


class BitcaskCLI:
    """Command-line interface for the Bitcask key-value store.

    This class provides methods for interacting with the Bitcask database
    through a command-line interface, including data operations and mode
    switching.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        debug_mode: Optional[bool] = None,
    ):
        """Initialize the Bitcask CLI.

        Args:
        ----
            data_dir: Directory where the database files will be stored
            debug_mode: Whether to run in debug mode (human-readable format)

        """
        self.data_dir = bitcask_config.get_data_dir(data_dir)
        self.debug_mode = (
            debug_mode if debug_mode is not None else bitcask_config.get_debug_mode()
        )
        self.db = None
        self.server_process = None
        self.server_url = None

    def ensure_db(self) -> None:
        """Ensure the database connection is established."""
        if self.db is None:
            self.db = Bitcask(
                str(self.data_dir),
                debug_mode=self.debug_mode,
            )
            atexit.register(self.close)

    def refresh_db(self) -> None:
        """Close and reopen the database connection."""
        self.close()
        self.ensure_db()

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
            msg = f"✓ Successfully stored value for key: {key}"
            click.echo(click.style(msg, fg="green"))
            self.refresh_db()  # Refresh after write
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def get(self, key: str) -> None:
        """Retrieve a value from the database."""
        try:
            self.ensure_db()
            value = self.db.get(key)
            if value is None:
                msg = f"✗ Key '{key}' not found"
                click.echo(click.style(msg, fg="yellow"))
                return
            click.echo(click.style(f"Value for key '{key}':", fg="blue"))
            click.echo(value)
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def delete(self, key: str) -> None:
        """Delete a value from the database."""
        try:
            self.ensure_db()
            self.db.delete(key)
            msg = f"✓ Successfully deleted key: {key}"
            click.echo(click.style(msg, fg="green"))
            self.refresh_db()  # Refresh after write
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def list_keys(self) -> None:
        """List all keys in the database."""
        try:
            self.ensure_db()
            keys = self.db.list_keys()
            if not keys:
                click.echo(click.style("No keys found in database", fg="yellow"))
                return
            click.echo(click.style("Available keys:", fg="blue"))
            for key in keys:
                click.echo(f"  • {key}")
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def clear(self) -> None:
        """Clear all data from the database."""
        try:
            self.ensure_db()
            self.db.clear()
            msg = "✓ Successfully cleared all data"
            click.echo(click.style(msg, fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def close(self) -> None:
        """Close the database connection."""
        if self.db is not None:
            self.db.close()
            self.db = None

    def switch_mode(self, debug_mode: bool) -> None:
        """Switch between debug and normal modes."""
        try:
            # Show warning and get confirmation
            mode = "debug" if debug_mode else "normal"
            msg = "⚠️ WARNING: Switching modes will delete ALL data!"
            click.echo(click.style(msg, fg="yellow", bold=True))
            click.echo(click.style("This action cannot be undone.", fg="yellow"))
            confirm_msg = f"Do you want to switch to {mode} mode?"
            if not click.confirm(click.style(confirm_msg, fg="yellow")):
                click.echo(click.style("Mode switch cancelled", fg="blue"))
                return

            # Close and clear the database
            if self.db is not None:
                self.db.close()
                self.db = None

            # Delete all data files and clear the directory
            if self.data_dir.exists():
                for file in self.data_dir.glob("*"):
                    if file.is_file():
                        file.unlink()
                # Recreate the directory if it was deleted
                self.data_dir.mkdir(exist_ok=True)

            # Switch mode and create new database
            self.debug_mode = debug_mode
            bitcask_config.set_debug_mode(debug_mode)  # Update global config
            self.db = Bitcask(str(self.data_dir), debug_mode=self.debug_mode)

            click.echo(click.style(f"✓ Switched to {mode} mode", fg="green"))
            click.echo(click.style("✓ Database cleared completely", fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)

    def start_server(self, port: int = 8000) -> None:
        """
        Starts the Bitcask server as a subprocess on the specified port.
        
        Initializes the server using the current configuration, sets up signal handlers for
        graceful shutdown, and displays server status and URL information in the CLI.
        
        Args:
            port: The port number on which to run the server (default is 8000).
        """
        try:
            msg = f"Starting Bitcask server on port {port}..."
            click.echo(click.style(msg, fg="blue"))

            # Get the server script path
            cwd = dirname(dirname(abspath(__file__)))
            server_script = Path(cwd) / "server.py"

            if not server_script.exists():
                click.echo(
                    click.style("✗ Error: Server script not found", fg="red"), err=True
                )
                return

            # Start the server process with the current configuration
            cmd = [
                "python",
                str(server_script),
                "--port",
                str(port),
                "--data-dir",
                str(self.data_dir),
                "--debug" if self.debug_mode else "",
            ]

            # Register signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                """
                Handles termination signals to gracefully shut down the server process.
                
                This function outputs a shutdown message, stops the running server, and exits the program when a termination signal is received.
                """
                click.echo(click.style("\nShutting down server...", fg="yellow"))
                self.stop_server()
                sys.exit(0)

            import signal

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            self.server_process = subprocess.Popen(cmd, cwd=cwd)
            atexit.register(self.stop_server)
            self.server_url = f"http://localhost:{port}"

            click.echo(click.style("✓ Server started successfully", fg="green"))
            click.echo(click.style(f"Server URL: {self.server_url}", fg="blue"))
            click.echo(click.style("Press Ctrl+C to stop the server", fg="yellow"))
        except Exception as e:
            msg = f"✗ Error starting server: {e}"
            click.echo(click.style(msg, fg="red"), err=True)

    def stop_server(self) -> None:
        """Stop the Bitcask server."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(
                    timeout=5
                )  # Wait up to 5 seconds for graceful shutdown
                click.echo(click.style("✓ Server stopped successfully", fg="green"))
            except subprocess.TimeoutExpired:
                self.server_process.kill()  # Force kill if graceful shutdown fails
                click.echo(click.style("! Server forcefully stopped", fg="yellow"))
            except Exception as e:
                click.echo(
                    click.style(f"✗ Error stopping server: {e}", fg="red"), err=True
                )
            finally:
                self.server_process = None
                self.server_url = None


@click.group()
@click.option("--data-dir", help="Data directory path")
@click.option("--debug", is_flag=True, help="Run in debug mode (human-readable format)")
@click.pass_context
def cli(ctx, data_dir, debug):
    """Bitcask CLI - A command-line interface for the Bitcask key-value store."""
    ctx.obj = BitcaskCLI(
        data_dir,
        debug_mode=debug,
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
    cli.list_keys()


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
    """Switch to normal mode (proto format)."""
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
@click.pass_obj
def view(cli: BitcaskCLI):
    """View current configuration."""
    try:
        if not cli.data_dir.exists():
            click.echo(click.style("No configuration file found", fg="yellow"))
            return

        with open(cli.data_dir / "config.json") as f:
            current_config = json.load(f)
            click.echo(click.style("Current configuration:", fg="blue"))
            click.echo(f"  • Debug mode: {current_config.get('debug_mode', False)}")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@config.command()
@click.pass_obj
def reset(cli: BitcaskCLI):
    """Reset all configuration settings to defaults."""
    try:
        bitcask_config.set_debug_mode(False)
        msg = "✓ Configuration reset to defaults"
        click.echo(click.style(msg, fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@cli.group()
def server():
    """Manage the Bitcask server."""
    pass


@server.command()
@click.option("--port", default=8000, help="Port to run the server on")
@click.pass_obj
def start(cli: BitcaskCLI, port: int):
    """Start the Bitcask server."""
    cli.start_server(port)


@server.command()
@click.pass_obj
def stop(cli: BitcaskCLI):
    """Stop the Bitcask server."""
    cli.stop_server()


if __name__ == "__main__":
    cli()

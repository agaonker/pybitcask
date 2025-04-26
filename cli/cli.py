"""
Command-line interface entry point for the Bitcask key-value store.

This module serves as the main entry point for the Bitcask CLI application.
It imports and runs the CLI implementation from the pybitcask_cli package.
"""

from pybitcask_cli.__main__ import cli

if __name__ == "__main__":
    cli()

"""Setup configuration for the Bitcask CLI package.

This module defines the package metadata and dependencies for the Bitcask CLI.
It uses setuptools to package the CLI application for distribution.
"""

from setuptools import find_packages, setup

setup(
    name="pybitcask-cli",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.0",
        "pybitcask>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "pbc=pybitcask_cli.__main__:cli",
        ],
    },
)

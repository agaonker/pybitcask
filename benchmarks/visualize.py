"""Visualization module for Bitcask benchmark results."""

# -*- coding: utf-8 -*-
import json
import os
import platform
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import psutil
import seaborn as sns


def get_system_info() -> Dict[str, str]:
    """
    Get system configuration information.

    Returns
    -------
        Dictionary containing system information

    """
    return {
        "OS": platform.system() + " " + platform.release(),
        "Python": platform.python_version(),
        "Processor": platform.processor(),
        "Memory": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        "CPU Cores": str(psutil.cpu_count(logical=False)),
        "CPU Threads": str(psutil.cpu_count(logical=True)),
    }


def load_results() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load benchmark results from file.

    Returns
    -------
        Dictionary containing benchmark results

    """
    with open("benchmarks/results/results.json") as f:
        return json.load(f)


def create_dataframe(results: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Create a DataFrame from benchmark results.

    Args:
    ----
        results: Dictionary containing benchmark results

    Returns:
    -------
        DataFrame with processed benchmark data

    """
    data = []
    for operation, measurements in results.items():
        for measurement in measurements:
            data.append(
                {
                    "operation": operation,
                    "data_size": measurement["data_size"],
                    "value_size": measurement["value_size"],
                    "time": measurement["time"],
                }
            )
    return pd.DataFrame(data)


def plot_operation_times(df: pd.DataFrame, operation: str, output_dir: str):
    """
    Plot operation times for different data sizes.

    Args:
    ----
        df: DataFrame containing benchmark data
        operation: Operation type to plot
        output_dir: Directory to save the plot

    """
    operation_data = df[df["operation"] == operation]
    plt.figure(figsize=(10, 6))

    for value_size in operation_data["value_size"].unique():
        data = operation_data[operation_data["value_size"] == value_size]
        plt.plot(
            data["data_size"],
            data["time"],
            marker="o",
            label=f"Value size: {value_size} bytes",
        )

    plt.xlabel("Data Size (number of key-value pairs)")
    plt.ylabel("Time per Operation (seconds)")
    plt.title(f"{operation.replace('_', ' ').title()} Time vs Data Size")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f"{operation}_time.png"))
    plt.close()


def plot_operation_comparison(df: pd.DataFrame, output_dir: str):
    """
    Plot comparison of different operations.

    Args:
    ----
        df: DataFrame containing benchmark data
        output_dir: Directory to save the plot

    """
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="operation", y="time")
    plt.xlabel("Operation")
    plt.ylabel("Time per Operation (seconds)")
    plt.title("Operation Time Comparison")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "operation_comparison.png"))
    plt.close()


def plot_value_size_impact(df: pd.DataFrame, output_dir: str):
    """
    Plot impact of value size on operation time.

    Args:
    ----
        df: DataFrame containing benchmark data
        output_dir: Directory to save the plot

    """
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=df, x="value_size", y="time", hue="operation")
    plt.xlabel("Value Size (bytes)")
    plt.ylabel("Time per Operation (seconds)")
    plt.title("Impact of Value Size on Operation Time")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "value_size_impact.png"))
    plt.close()


def generate_plots(results: Dict[str, List[Dict[str, Any]]], output_dir: str):
    """
    Generate all benchmark plots.

    Args:
    ----
        results: Dictionary containing benchmark results
        output_dir: Directory to save the plots

    """
    os.makedirs(output_dir, exist_ok=True)
    df = create_dataframe(results)

    for operation in results.keys():
        plot_operation_times(df, operation, output_dir)

    plot_operation_comparison(df, output_dir)
    plot_value_size_impact(df, output_dir)


def generate_benchmark_report(
    results: Dict[str, List[Dict[str, Any]]], output_dir: str
):
    """
    Generate a markdown report of benchmark results.

    Args:
    ----
        results: Dictionary containing benchmark results
        output_dir: Directory to save the report

    """
    os.makedirs(output_dir, exist_ok=True)
    df = create_dataframe(results)

    # Calculate summary statistics
    summary = (
        df.groupby(["operation", "value_size"])["time"]
        .agg(["mean", "std", "min", "max"])
        .round(6)
    )

    # Generate report
    report = ["# Bitcask Benchmark Report\n"]

    # Add system information
    report.append("## System Configuration\n")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        report.append(f"- **{key}:** {value}")
    report.append("\n")

    # Add summary statistics
    report.append("## Performance Summary\n")
    report.append(summary.to_markdown())
    report.append("\n")

    # Write report
    with open(os.path.join(output_dir, "benchmark_report.md"), "w") as f:
        f.write("\n".join(report))


if __name__ == "__main__":
    # Load results
    results = load_results()

    # Generate plots
    generate_plots(results, "benchmarks/plots")

    # Generate and save report
    generate_benchmark_report(results, "benchmarks/results")

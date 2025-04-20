"""Benchmark suite for measuring Bitcask key-value store performance."""

# -*- coding: utf-8 -*-
import json
import os
import random
import shutil
import statistics
import string
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pybitcask import Bitcask


class BenchmarkBase:
    """Base class for benchmark implementations."""

    def __init__(self):
        """Initialize benchmark configuration."""
        self.data_dir = Path("benchmark_data")
        self.db = None

    def setup(self):
        """Set up the benchmark environment."""
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def cleanup(self):
        """Clean up the benchmark environment."""
        if self.db:
            self.db.close()
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

    def generate_data(self, size: int, value_size: int) -> Dict[str, str]:
        """
        Generate test data for benchmarking.

        Args:
        ----
            size: Number of key-value pairs to generate
            value_size: Size of each value in bytes

        Returns:
        -------
            Dictionary containing test data

        """
        return {f"key{i}": "x" * value_size for i in range(size)}


class PyBitcaskEngine:
    """Engine class for running Bitcask benchmarks."""

    def __init__(self, path: str):
        """
        Initialize the Bitcask engine.

        Args:
        ----
            path: Path to the data directory

        """
        self.path = path
        Path(path).mkdir(parents=True, exist_ok=True)
        self.db = None

    def setup(self):
        """Set up the Bitcask instance."""
        self.db = Bitcask(self.path)

    def teardown(self):
        """Clean up the Bitcask instance."""
        if self.db:
            self.db.close()

    def put(self, key: str, value: str):
        """
        Store a key-value pair.

        Args:
        ----
            key: The key to store
            value: The value to store

        """
        self.db.put(key, value)

    def get(self, key: str) -> str:
        """
        Retrieve a value by key.

        Args:
        ----
            key: The key to retrieve

        Returns:
        -------
            The value associated with the key

        """
        return self.db.get(key)

    def delete(self, key: str):
        """
        Delete a key-value pair.

        Args:
        ----
            key: The key to delete

        """
        self.db.delete(key)


class BitcaskBenchmark:
    """Benchmark class for measuring Bitcask performance metrics."""

    def __init__(self):
        """Initialize benchmark configuration and setup test data."""
        self.data_dir = "benchmark_data"
        self.db = None
        self.data_sizes = [100, 1000, 10000]
        self.value_sizes = [64, 256, 1024]  # in bytes

    def setup(self):
        """Set up the benchmark environment."""
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def generate_data(self, size: int, value_size: int) -> Dict[str, str]:
        """
        Generate test data for benchmarking.

        Args:
        ----
            size: Number of key-value pairs to generate
            value_size: Size of each value in bytes

        Returns:
        -------
            Dictionary containing test data

        """
        return {f"key{i}": "x" * value_size for i in range(size)}

    def run_write_benchmark(self, size: int, value_size: int) -> float:
        """
        Run write operation benchmark.

        Args:
        ----
            size: Number of key-value pairs to write
            value_size: Size of each value in bytes

        Returns:
        -------
            Average time per operation in seconds

        """
        data = self.generate_data(size, value_size)
        self.db = Bitcask(self.data_dir)

        start_time = time.time()
        for key, value in data.items():
            self.db.put(key, value)
        end_time = time.time()

        self.db.close()
        return (end_time - start_time) / size

    def run_read_benchmark(self, size: int, value_size: int) -> float:
        """
        Run read operation benchmark.

        Args:
        ----
            size: Number of key-value pairs to read
            value_size: Size of each value in bytes

        Returns:
        -------
            Average time per operation in seconds

        """
        data = self.generate_data(size, value_size)
        self.db = Bitcask(self.data_dir)

        # Write data first
        for key, value in data.items():
            self.db.put(key, value)

        # Benchmark reads
        start_time = time.time()
        for key in data.keys():
            self.db.get(key)
        end_time = time.time()

        self.db.close()
        return (end_time - start_time) / size


def generate_random_data(size: int, value_size: int = 100) -> List[Tuple[str, str]]:
    """
    Generate random key-value pairs for testing.

    Args:
    ----
        size: Number of key-value pairs to generate
        value_size: Size of each value in bytes

    Returns:
    -------
        List of (key, value) tuples

    """
    data = []
    for _ in range(size):
        key = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        value = "".join(
            random.choices(string.ascii_letters + string.digits, k=value_size)
        )
        data.append((key, value))
    return data


def run_benchmark(
    engine: PyBitcaskEngine, data: List[Tuple[str, str]], operations: int = 1000
) -> Dict[str, float]:
    """
    Run benchmark tests on pybitcask.

    Args:
    ----
        engine: The Bitcask engine to test
        data: List of (key, value) pairs to use
        operations: Number of operations to perform

    Returns:
    -------
        Dictionary of benchmark results

    """
    results = {
        "write_times": [],
        "read_times": [],
        "delete_times": [],
        "batch_write_times": [],
        "sequential_read_times": [],
        "random_read_times": [],
    }

    # Setup
    engine.setup()

    print("\nRunning Write Benchmark...")
    # Write benchmark
    for key, value in data[:operations]:
        start = time.perf_counter()
        engine.put(key, value)
        results["write_times"].append(time.perf_counter() - start)

    print("Running Read Benchmark...")
    # Read benchmark (sequential)
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.get(key)
        results["sequential_read_times"].append(time.perf_counter() - start)

    print("Running Random Read Benchmark...")
    # Random read benchmark
    random_keys = random.sample([key for key, _ in data[:operations]], operations)
    for key in random_keys:
        start = time.perf_counter()
        engine.get(key)
        results["random_read_times"].append(time.perf_counter() - start)

    print("Running Delete Benchmark...")
    # Delete benchmark
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.delete(key)
        results["delete_times"].append(time.perf_counter() - start)

    # Batch write benchmark
    print("Running Batch Write Benchmark...")
    batch_size = 100
    for i in range(0, operations, batch_size):
        batch_data = data[i : i + batch_size]
        start = time.perf_counter()
        for key, value in batch_data:
            engine.put(key, value)
        results["batch_write_times"].append((time.perf_counter() - start) / batch_size)

    # Teardown
    engine.teardown()

    # Calculate statistics
    stats = {}
    for op_type, times in results.items():
        if times:  # Only calculate if we have data
            stats[f"{op_type}_avg"] = statistics.mean(times)
            stats[f"{op_type}_std"] = statistics.stdev(times)
            stats[f"{op_type}_min"] = min(times)
            stats[f"{op_type}_max"] = max(times)

    return stats


def run_benchmarks() -> Dict[str, List[Dict[str, Any]]]:
    """
    Run all benchmarks and collect results.

    Returns
    -------
        Dictionary containing benchmark results for different operations

    """
    benchmark = BitcaskBenchmark()
    results = {
        "write": [],
        "read": [],
        "random_read": [],
        "batch_write": [],
        "delete": [],
    }

    for size in benchmark.data_sizes:
        for value_size in benchmark.value_sizes:
            # Run write benchmark
            write_time = benchmark.run_write_benchmark(size, value_size)
            results["write"].append(
                {"data_size": size, "value_size": value_size, "time": write_time}
            )

            # Run read benchmark
            read_time = benchmark.run_read_benchmark(size, value_size)
            results["read"].append(
                {"data_size": size, "value_size": value_size, "time": read_time}
            )

            # Clean up between runs
            benchmark.setup()

    return results


def main():
    """Run the benchmark suite and save results."""
    # Configuration
    data_sizes = [1000, 10000, 100000]
    value_sizes = [100, 1000, 10000]  # Different value sizes in bytes
    operations = 1000

    all_results = {}

    for data_size in data_sizes:
        for value_size in value_sizes:
            msg = f"\nRunning benchmark with data_size={data_size}, value_size={value_size}"
            print(msg)

            # Generate test data
            data = generate_random_data(data_size, value_size)

            # Run benchmarks
            db_path = f"benchmarks/data/pybitcask_{data_size}_{value_size}"
            engine = PyBitcaskEngine(db_path)
            results = run_benchmark(engine, data, min(operations, data_size))

            # Store results
            all_results[f"size_{data_size}_value_{value_size}"] = {
                "data_size": data_size,
                "value_size": value_size,
                "operations": min(operations, data_size),
                "metrics": results,
            }

    # Save results
    Path("benchmarks/results").mkdir(parents=True, exist_ok=True)
    with open("benchmarks/results/benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print("\nBenchmark Results Summary:")
    print("=" * 80)
    for config, results in all_results.items():
        print(f"\nConfiguration: {config}")
        metrics = results["metrics"]
        print(
            f"Data Size: {results['data_size']}, "
            f"Value Size: {results['value_size']} bytes"
        )
        print(
            f"Sequential Write: {metrics['write_times_avg']:.6f} ± "
            f"{metrics['write_times_std']:.6f} seconds"
        )
        print(
            f"Sequential Read:  {metrics['sequential_read_times_avg']:.6f} ± "
            f"{metrics['sequential_read_times_std']:.6f} seconds"
        )
        print(
            f"Random Read:     {metrics['random_read_times_avg']:.6f} ± "
            f"{metrics['random_read_times_std']:.6f} seconds"
        )
        print(
            f"Batch Write:     {metrics['batch_write_times_avg']:.6f} ± "
            f"{metrics['batch_write_times_std']:.6f} seconds"
        )
        print(
            f"Delete:          {metrics['delete_times_avg']:.6f} ± "
            f"{metrics['delete_times_std']:.6f} seconds"
        )


if __name__ == "__main__":
    main()

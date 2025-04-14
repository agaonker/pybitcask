import time
import random
import string
import json
import os
from pathlib import Path
import statistics
from typing import Dict, List, Tuple
from pybitcask import Bitcask

class PyBitcaskEngine:
    def __init__(self, path: str):
        self.path = path
        Path(path).mkdir(parents=True, exist_ok=True)
        self.db = None
    
    def setup(self):
        self.db = Bitcask(self.path)
    
    def teardown(self):
        if self.db:
            self.db.close()
    
    def put(self, key: str, value: str):
        self.db.put(key, value)
    
    def get(self, key: str) -> str:
        return self.db.get(key)
    
    def delete(self, key: str):
        self.db.delete(key)

def generate_random_data(size: int, value_size: int = 100) -> List[Tuple[str, str]]:
    """Generate random key-value pairs."""
    data = []
    for _ in range(size):
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        value = ''.join(random.choices(string.ascii_letters + string.digits, k=value_size))
        data.append((key, value))
    return data

def run_benchmark(engine: PyBitcaskEngine, data: List[Tuple[str, str]], 
                 operations: int = 1000) -> Dict[str, float]:
    """Run benchmark tests on pybitcask."""
    results = {
        'write_times': [],
        'read_times': [],
        'delete_times': [],
        'batch_write_times': [],
        'sequential_read_times': [],
        'random_read_times': []
    }
    
    # Setup
    engine.setup()
    
    print("\nRunning Write Benchmark...")
    # Write benchmark
    for key, value in data[:operations]:
        start = time.perf_counter()
        engine.put(key, value)
        results['write_times'].append(time.perf_counter() - start)
    
    print("Running Read Benchmark...")
    # Read benchmark (sequential)
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.get(key)
        results['sequential_read_times'].append(time.perf_counter() - start)
    
    print("Running Random Read Benchmark...")
    # Random read benchmark
    random_keys = random.sample([key for key, _ in data[:operations]], operations)
    for key in random_keys:
        start = time.perf_counter()
        engine.get(key)
        results['random_read_times'].append(time.perf_counter() - start)
    
    print("Running Delete Benchmark...")
    # Delete benchmark
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.delete(key)
        results['delete_times'].append(time.perf_counter() - start)
    
    # Batch write benchmark
    print("Running Batch Write Benchmark...")
    batch_size = 100
    for i in range(0, operations, batch_size):
        batch_data = data[i:i+batch_size]
        start = time.perf_counter()
        for key, value in batch_data:
            engine.put(key, value)
        results['batch_write_times'].append((time.perf_counter() - start) / batch_size)
    
    # Teardown
    engine.teardown()
    
    # Calculate statistics
    stats = {}
    for op_type, times in results.items():
        if times:  # Only calculate if we have data
            stats[f'{op_type}_avg'] = statistics.mean(times)
            stats[f'{op_type}_std'] = statistics.stdev(times)
            stats[f'{op_type}_min'] = min(times)
            stats[f'{op_type}_max'] = max(times)
    
    return stats

def main():
    # Configuration
    data_sizes = [1000, 10000, 100000]
    value_sizes = [100, 1000, 10000]  # Different value sizes in bytes
    operations = 1000
    
    all_results = {}
    
    for data_size in data_sizes:
        for value_size in value_sizes:
            print(f"\nRunning benchmark with data_size={data_size}, value_size={value_size}")
            
            # Generate test data
            data = generate_random_data(data_size, value_size)
            
            # Run benchmarks
            engine = PyBitcaskEngine(f"benchmarks/data/pybitcask_{data_size}_{value_size}")
            results = run_benchmark(engine, data, min(operations, data_size))
            
            # Store results
            all_results[f"size_{data_size}_value_{value_size}"] = {
                "data_size": data_size,
                "value_size": value_size,
                "operations": min(operations, data_size),
                "metrics": results
            }
    
    # Save results
    Path('benchmarks/results').mkdir(parents=True, exist_ok=True)
    with open('benchmarks/results/benchmark_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("\nBenchmark Results Summary:")
    print("=" * 80)
    for config, results in all_results.items():
        print(f"\nConfiguration: {config}")
        metrics = results['metrics']
        print(f"Data Size: {results['data_size']}, Value Size: {results['value_size']} bytes")
        print(f"Sequential Write: {metrics['write_times_avg']:.6f} ± {metrics['write_times_std']:.6f} seconds")
        print(f"Sequential Read:  {metrics['sequential_read_times_avg']:.6f} ± {metrics['sequential_read_times_std']:.6f} seconds")
        print(f"Random Read:     {metrics['random_read_times_avg']:.6f} ± {metrics['random_read_times_std']:.6f} seconds")
        print(f"Batch Write:     {metrics['batch_write_times_avg']:.6f} ± {metrics['batch_write_times_std']:.6f} seconds")
        print(f"Delete:          {metrics['delete_times_avg']:.6f} ± {metrics['delete_times_std']:.6f} seconds")

if __name__ == "__main__":
    main() 
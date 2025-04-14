import time
import random
import string
import json
import os
from pathlib import Path
import statistics
from typing import Dict, List, Tuple
import sqlite3
import lmdb
from pybitcask import Bitcask

class StorageEngine:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        Path(path).mkdir(parents=True, exist_ok=True)
    
    def setup(self):
        raise NotImplementedError
    
    def teardown(self):
        raise NotImplementedError
    
    def put(self, key: str, value: str):
        raise NotImplementedError
    
    def get(self, key: str) -> str:
        raise NotImplementedError
    
    def delete(self, key: str):
        raise NotImplementedError

class PyBitcaskEngine(StorageEngine):
    def setup(self):
        self.db = Bitcask(self.path)
    
    def teardown(self):
        self.db.close()
    
    def put(self, key: str, value: str):
        self.db.put(key, value)
    
    def get(self, key: str) -> str:
        return self.db.get(key)
    
    def delete(self, key: str):
        self.db.delete(key)

class SQLiteEngine(StorageEngine):
    def setup(self):
        self.conn = sqlite3.connect(os.path.join(self.path, 'test.db'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)')
    
    def teardown(self):
        self.conn.close()
    
    def put(self, key: str, value: str):
        self.cursor.execute('INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()
    
    def get(self, key: str) -> str:
        self.cursor.execute('SELECT value FROM kv WHERE key = ?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def delete(self, key: str):
        self.cursor.execute('DELETE FROM kv WHERE key = ?', (key,))
        self.conn.commit()

class LMDBEngine(StorageEngine):
    def setup(self):
        self.env = lmdb.open(self.path, map_size=1024*1024*1024)
        self.txn = self.env.begin(write=True)
    
    def teardown(self):
        self.txn.commit()
        self.env.close()
    
    def put(self, key: str, value: str):
        self.txn.put(key.encode(), value.encode())
    
    def get(self, key: str) -> str:
        value = self.txn.get(key.encode())
        return value.decode() if value else None
    
    def delete(self, key: str):
        self.txn.delete(key.encode())

def generate_random_data(size: int) -> List[Tuple[str, str]]:
    """Generate random key-value pairs."""
    data = []
    for _ in range(size):
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        value = ''.join(random.choices(string.ascii_letters + string.digits, k=100))
        data.append((key, value))
    return data

def run_benchmark(engine: StorageEngine, data: List[Tuple[str, str]], 
                 operations: int = 1000) -> Dict[str, float]:
    """Run benchmark tests on the storage engine."""
    results = {
        'write_times': [],
        'read_times': [],
        'delete_times': []
    }
    
    # Setup
    engine.setup()
    
    # Write benchmark
    for key, value in data[:operations]:
        start = time.perf_counter()
        engine.put(key, value)
        results['write_times'].append(time.perf_counter() - start)
    
    # Read benchmark
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.get(key)
        results['read_times'].append(time.perf_counter() - start)
    
    # Delete benchmark
    for key, _ in data[:operations]:
        start = time.perf_counter()
        engine.delete(key)
        results['delete_times'].append(time.perf_counter() - start)
    
    # Teardown
    engine.teardown()
    
    # Calculate statistics
    return {
        'write_avg': statistics.mean(results['write_times']),
        'write_std': statistics.stdev(results['write_times']),
        'read_avg': statistics.mean(results['read_times']),
        'read_std': statistics.stdev(results['read_times']),
        'delete_avg': statistics.mean(results['delete_times']),
        'delete_std': statistics.stdev(results['delete_times'])
    }

def main():
    # Configuration
    data_size = 10000
    operations = 1000
    engines = [
        ('pybitcask', PyBitcaskEngine),
        ('sqlite', SQLiteEngine),
        ('lmdb', LMDBEngine)
    ]
    
    # Generate test data
    data = generate_random_data(data_size)
    
    # Run benchmarks
    results = {}
    for name, engine_class in engines:
        print(f"\nRunning benchmarks for {name}...")
        engine = engine_class(name, f"benchmarks/data/{name}")
        results[name] = run_benchmark(engine, data, operations)
    
    # Save results
    with open('benchmarks/results/benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print results
    print("\nBenchmark Results:")
    print("=" * 80)
    for engine, stats in results.items():
        print(f"\n{engine.upper()}:")
        print(f"Write: {stats['write_avg']:.6f} ± {stats['write_std']:.6f} seconds")
        print(f"Read:  {stats['read_avg']:.6f} ± {stats['read_std']:.6f} seconds")
        print(f"Delete: {stats['delete_avg']:.6f} ± {stats['delete_std']:.6f} seconds")

if __name__ == "__main__":
    main() 
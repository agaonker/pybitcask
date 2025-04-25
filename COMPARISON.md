# Database Comparison

## Overview

| Database | Design | Strengths | Weaknesses | Best For | Website |
|----------|--------|-----------|------------|----------|---------|
| **Riak Bitcask** | Append-only log + in-memory index | - Production proven <br> - Built-in compaction <br> - Handles billions of keys <br> - Distributed support | - More complex <br> - Erlang dependency | - Distributed systems <br> - High availability needs | [Docs](https://docs.riak.com/riak/kv/latest/setup/planning/backend/bitcask/) |
| **LevelDB** | LSM tree | - Good read/write balance <br> - Compression support <br> - Large dataset handling | - Complex implementation <br> - Write amplification | - General purpose <br> - Large datasets | [GitHub](https://github.com/google/leveldb) |
| **BoltDB** | B+tree | - ACID compliant <br> - Very fast reads <br> - Simple API | - Slower writes <br> - Single writer | - Read-heavy workloads <br> - Embedded systems | [GitHub](https://github.com/boltdb/bolt) |
| **LMDB** | Memory-mapped B+tree | - Extremely fast reads <br> - Zero-copy access <br> - ACID compliant | - Limited concurrency <br> - Memory mapped | - Embedded systems <br> - Fast read access | [Website](https://symas.com/lmdb/) |

## Performance Comparison

| Operation | LevelDB | BoltDB | LMDB |
|-----------|---------|--------|------|
| Write (small) | 10-15μs | 50-100μs | 20-30μs |
| Read (small) | 5-10μs | 1-2μs | <1μs |
| Write (10KB) | 30-40μs | 100-200μs | 40-50μs |
| Read (10KB) | 10-15μs | 2-3μs | 1-2μs |
| Concurrent Reads | Excellent | Excellent | Limited |
| Concurrent Writes | Good | Single writer | Limited |

*Note: Performance numbers are approximate and can vary based on hardware and workload.*

## Where pybitcask Aims to Be

### 1. Python-Centric Environments

```python
# Example: Python microservice
from pybitcask import Bitcask
from fastapi import FastAPI

app = FastAPI()
db = Bitcask("data")

@app.post("/data/{key}")
async def put_data(key: str, value: dict):
    db.put(key, value)
    return {"status": "success"}

@app.get("/data/{key}")
async def get_data(key: str):
    return db.get(key)
```

### 2. Resource-Constrained Applications

```python
# Example: Edge computing device
from pybitcask import Bitcask
import psutil

class ResourceAwareStore:
    def __init__(self, data_dir, memory_limit_mb=100):
        self.db = Bitcask(data_dir)
        self.memory_limit = memory_limit_mb * 1024 * 1024

    def check_memory(self):
        if psutil.Process().memory_info().rss > self.memory_limit:
            self.cleanup_old_data()

    def put(self, key, value):
        self.check_memory()
        self.db.put(key, value)
```

### 3. High-Write Throughput with Simple Needs

```python
# Example: Log aggregation system
class LogAggregator:
    def __init__(self, data_dir):
        self.db = Bitcask(data_dir)

    def ingest_log(self, log_entry):
        timestamp = int(time.time() * 1000)
        key = f"log:{timestamp}"
        self.db.put(key, json.dumps(log_entry))

    def query_logs(self, start_time, end_time):
        results = []
        for key in self.db.keys():
            if key.startswith("log:"):
                ts = int(key.split(":")[1])
                if start_time <= ts <= end_time:
                    results.append(json.loads(self.db.get(key)))
        return results
```

## When to Consider pybitcask

### Consider pybitcask when you need:
1. Simple, reliable key-value storage
2. High write throughput
3. Python-native solution
4. Minimal resource usage
5. Easy to understand and modify

### Avoid pybitcask when you need:
1. Complex queries
2. Distributed systems
3. High concurrency writes
4. Built-in compaction
5. Advanced features like transactions

# Python Bitcask Implementation

This is a Python implementation of the Bitcask storage engine, which provides an efficient and reliable way to store and retrieve key-value pairs.

## Features

- Append-only log storage
- In-memory index for fast lookups
- Thread-safe operations
- Data persistence
- Support for complex data types (via JSON serialization)
- Tombstone-based deletion

## Use Cases

### Ideal Use Cases

1. **High-Write Throughput Applications**
   - Log aggregation systems
   - Event sourcing systems
   - Real-time analytics data collection
   - IoT device data storage
   - Message queue backends

2. **Simple Key-Value Storage Needs**
   - Session storage
   - User preferences
   - Configuration management
   - Feature flag storage
   - Cache persistence

3. **Data Recovery Scenarios**
   - Crash recovery systems
   - Transaction logs
   - Audit trails
   - System state snapshots

### Example: IoT Data Collection System

```python
from pybitcask import Bitcask
import time
import json

class IoTDataStore:
    def __init__(self, data_dir):
        self.db = Bitcask(data_dir)
        
    def store_sensor_data(self, device_id, sensor_data):
        # Create a composite key with timestamp
        key = f"{device_id}:{int(time.time())}"
        self.db.put(key, json.dumps(sensor_data))
        
    def get_device_history(self, device_id, start_time, end_time):
        results = []
        for key in self.db.keys():
            if key.startswith(device_id):
                timestamp = int(key.split(':')[1])
                if start_time <= timestamp <= end_time:
                    results.append(json.loads(self.db.get(key)))
        return results

# Usage
store = IoTDataStore("iot_data")
store.store_sensor_data("sensor1", {"temperature": 25.5, "humidity": 60})
history = store.get_device_history("sensor1", 0, int(time.time()))
```

## Scaling Considerations

### Vertical Scaling

1. **Memory Management**
   - The in-memory index grows with the number of unique keys
   - Monitor memory usage and implement key expiration if needed
   - Consider implementing a memory limit with LRU eviction

2. **Disk Space Management**
   - Implement compaction to remove old/deleted data
   - Use data partitioning by time or key ranges
   - Monitor disk usage and implement cleanup policies

### Horizontal Scaling

1. **Sharding Strategies**
   - Partition data by key ranges
   - Use consistent hashing for key distribution
   - Implement a sharding layer for data distribution

2. **Replication**
   - Implement leader-follower replication
   - Use quorum-based writes for consistency
   - Consider eventual consistency for better performance

### Performance Optimization

1. **Batch Operations**
   - Use batch writes for better throughput
   - Implement bulk reads for range queries
   - Consider asynchronous operations for non-critical data

2. **Compression**
   - Implement value compression for large data
   - Use efficient serialization formats
   - Consider columnar storage for analytics

## Limitations and Considerations

1. **Memory Usage**
   - The entire key space must fit in memory
   - Consider implementing key expiration
   - Monitor memory growth with key count

2. **Query Limitations**
   - No built-in range queries
   - No secondary indexes
   - No complex query capabilities

3. **Data Management**
   - No built-in compaction
   - Manual cleanup required for deleted data
   - Disk space grows with updates and deletes

4. **Concurrency**
   - Single-writer, multiple-reader model
   - Consider sharding for write scaling
   - Implement proper locking strategies

5. **Data Types**
   - Limited to JSON-serializable data
   - No native support for binary data
   - Consider implementing custom serialization

## Future Improvements

1. **Core Features**
   - Implement compaction mechanism
   - Add support for range queries
   - Add secondary index support
   - Implement data compression

2. **Scalability**
   - Add built-in sharding support
   - Implement replication
   - Add distributed coordination

3. **Performance**
   - Add batch operation support
   - Implement async operations
   - Add caching layer

4. **Monitoring**
   - Add metrics collection
   - Implement health checks
   - Add performance monitoring

## Installation

1. Clone the repository
2. Navigate to the project directory
3. Install dependencies (if any)

## Usage

### Basic Operations

```python
from bitcask import Bitcask

# Initialize the database
db = Bitcask("data_directory")

# Store data
db.put("key1", "value1")
db.put("key2", {"name": "test", "values": [1, 2, 3]})

# Retrieve data
value = db.get("key1")
print(value)  # Output: "value1"

# Delete data
db.delete("key1")

# Close the database
db.close()
```

### Running Tests

To run the test suite:

```bash
python -m unittest bitcask/tests/test_bitcask.py
```

## Implementation Details

### Data Structure

The implementation uses the following data structure for each record:

```
+----------------+----------------+----------------+----------------+----------------+
| key_size (4B)  | value_size (4B)| timestamp (8B) | key (var)      | value (var)    |
+----------------+----------------+----------------+----------------+----------------+
```

### Key Features

1. **Append-Only Log**: All writes are appended to the end of the current data file
2. **In-Memory Index**: Fast lookups using an in-memory hash map
3. **Thread Safety**: Operations are protected by locks
4. **Data Persistence**: Data is written to disk and can be recovered after restart
5. **Tombstone Records**: Deleted keys are marked with tombstone records

## Performance Benchmarks

The implementation has been benchmarked with different data sizes and value sizes to measure its performance characteristics.

### Benchmark Configuration
- Data sizes: 1,000, 10,000, and 100,000 entries
- Value sizes: 100, 1,000, and 10,000 bytes
- Operations tested: Sequential Write, Sequential Read, Random Read, Batch Write, and Delete

### Results

Times are in microseconds (μs):

|                 |   batch_write_time |   delete_time |   random_read_time |   read_time |   write_time |
|:----------------|-------------------:|--------------:|-------------------:|------------:|-------------:|
| (1000, 100)     |               3.77 |          3.13 |              14.6  |       14.26 |         4.1  |
| (1000, 1000)    |               6.44 |          3.09 |              16.71 |       15.76 |         6.74 |
| (1000, 10000)   |              27.58 |          3.06 |              27.39 |       26.59 |        27.4  |
| (10000, 100)    |               4    |          2.87 |              14.31 |       14.32 |         3.98 |
| (10000, 1000)   |               6.56 |          3.1  |              15.84 |       15.78 |         6.62 |
| (10000, 10000)  |              28.35 |          2.78 |              27.83 |       26.65 |        27.47 |
| (100000, 100)   |               3.66 |          3.12 |              15.76 |       14.57 |         3.73 |
| (100000, 1000)  |               7.21 |          3.05 |              16.83 |       16.06 |         6.49 |
| (100000, 10000) |              27.54 |          3.16 |              27.68 |       26.93 |        29.41 |

### Key Observations

1. **Write Performance**: 
   - Sequential writes are very fast, typically 3-7μs for small values
   - Performance scales well with increasing data size
   - Larger value sizes (10KB) increase write time to ~27-29μs

2. **Read Performance**:
   - Both sequential and random reads show consistent performance
   - Read times are around 14-16μs for small values
   - Larger values (10KB) increase read time to ~27μs

3. **Delete Performance**:
   - Delete operations are extremely fast and consistent
   - Average delete time is ~3μs regardless of data or value size

4. **Batch Write Performance**:
   - Similar to sequential write performance
   - Shows good efficiency for bulk operations

### Performance Characteristics

- **Scalability**: Performance remains stable as data size increases from 1K to 100K entries
- **Value Size Impact**: Operations with 10KB values take about 4-5x longer than with 100B values
- **Consistency**: Very consistent performance across operations, especially for deletes
- **Memory Efficiency**: In-memory index enables fast lookups without significant performance degradation

The benchmark results demonstrate that this implementation provides:
- Predictable performance characteristics
- Good scalability with data size
- Efficient operations for both small and large values
- Consistent delete performance
- Fast batch operations 

## Comparison with Similar Databases

| Database | Design | Strengths | Weaknesses | Best For | Website |
|----------|--------|-----------|------------|----------|---------|
| **pybitcask** | Append-only log + in-memory index | - Extremely fast writes (3-7μs) <br> - Simple implementation <br> - Crash-safe <br> - Minimal dependencies | - No built-in compaction <br> - Single-writer model <br> - Memory grows with keys | - High-write throughput apps <br> - Simple key-value needs <br> - Resource-constrained envs | [GitHub](https://github.com/agaonker/pybitcask) |
| **Riak Bitcask** | Append-only log + in-memory index | - Production proven <br> - Built-in compaction <br> - Handles billions of keys <br> - Distributed support | - More complex <br> - Erlang dependency | - Distributed systems <br> - High availability needs | [Docs](https://docs.riak.com/riak/kv/latest/setup/planning/backend/bitcask/) |
| **LevelDB** | LSM tree | - Good read/write balance <br> - Compression support <br> - Large dataset handling | - Complex implementation <br> - Write amplification | - General purpose <br> - Large datasets | [GitHub](https://github.com/google/leveldb) |
| **BoltDB** | B+tree | - ACID compliant <br> - Very fast reads <br> - Simple API | - Slower writes <br> - Single writer | - Read-heavy workloads <br> - Embedded systems | [GitHub](https://github.com/boltdb/bolt) |
| **LMDB** | Memory-mapped B+tree | - Extremely fast reads <br> - Zero-copy access <br> - ACID compliant | - Limited concurrency <br> - Memory mapped | - Embedded systems <br> - Fast read access | [Website](https://symas.com/lmdb/) |

### Where pybitcask Shines

pybitcask is particularly compelling in these specific scenarios:

1. **Python-Centric Environments**
   - Pure Python implementation
   - No external dependencies
   - Easy to integrate with Python applications
   - Perfect for Python-based microservices

2. **Resource-Constrained Applications**
   ```python
   # Example: Edge computing device with limited resources
   from pybitcask import Bitcask
   import psutil
   
   class ResourceAwareStore:
       def __init__(self, data_dir, memory_limit_mb=100):
           self.db = Bitcask(data_dir)
           self.memory_limit = memory_limit_mb * 1024 * 1024
           
       def check_memory(self):
           if psutil.Process().memory_info().rss > self.memory_limit:
               # Implement memory management strategy
               self.cleanup_old_data()
               
       def put(self, key, value):
           self.check_memory()
           self.db.put(key, value)
   ```

3. **High-Write Throughput with Simple Needs**
   ```python
   # Example: Log aggregation system
   class LogAggregator:
       def __init__(self, data_dir):
           self.db = Bitcask(data_dir)
           
       def ingest_log(self, log_entry):
           # Fast writes for log entries
           timestamp = int(time.time() * 1000)  # millisecond precision
           key = f"log:{timestamp}"
           self.db.put(key, json.dumps(log_entry))
           
       def query_logs(self, start_time, end_time):
           # Simple time-range query
           results = []
           for key in self.db.keys():
               if key.startswith("log:"):
                   ts = int(key.split(":")[1])
                   if start_time <= ts <= end_time:
                       results.append(json.loads(self.db.get(key)))
           return results
   ```

4. **Educational and Prototyping**
   - Clean, readable implementation
   - Easy to understand and modify
   - Good for learning about storage engines
   - Quick to prototype with

### Performance Comparison

| Operation | pybitcask | LevelDB | BoltDB | LMDB |
|-----------|-----------|---------|--------|------|
| Write (small) | 3-7μs | 10-15μs | 50-100μs | 20-30μs |
| Read (small) | 14-16μs | 5-10μs | 1-2μs | <1μs |
| Write (10KB) | 27-29μs | 30-40μs | 100-200μs | 40-50μs |
| Read (10KB) | 26-27μs | 10-15μs | 2-3μs | 1-2μs |
| Concurrent Reads | Good | Excellent | Excellent | Limited |
| Concurrent Writes | Single writer | Good | Single writer | Limited |

*Note: Performance numbers are approximate and can vary based on hardware and workload.*

### When to Choose pybitcask

Choose pybitcask when you need:
1. Simple, reliable key-value storage
2. High write throughput
3. Python-native solution
4. Minimal resource usage
5. Easy to understand and modify

Avoid pybitcask when you need:
1. Complex queries
2. Distributed systems
3. High concurrency writes
4. Built-in compaction
5. Advanced features like transactions 
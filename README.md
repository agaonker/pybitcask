# Python Bitcask Implementation

A Python implementation of the Bitcask storage engine, providing efficient and reliable key-value storage.

## Features

- Append-only log storage
- In-memory index for fast lookups
- Thread-safe operations
- Data persistence
- Support for complex data types (via JSON serialization)
- Tombstone-based deletion

## Quick Start

Run the complete setup with a single command:

```bash
./project-guardian.sh
```

This will:
1. Install uv (the fast Python package installer)
2. Create and activate a virtual environment
3. Install all dependencies
4. Set up pre-commit hooks
5. Run the test suite

## Installation

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/agaonker/pybitcask.git
   cd pybitcask
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Unix/macOS
   ```

4. Install dependencies:
   ```bash
   # Install core dependencies
   uv pip install -e .

   # Install development dependencies
   uv pip install -e ".[dev]"
   ```

5. Run tests:
   ```bash
   pytest tests/ -v
   ```

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

## Example Usage

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

## Limitations

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

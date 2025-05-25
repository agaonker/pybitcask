# Python Bitcask Implementation

A Python implementation of the Bitcask storage engine, providing efficient and reliable key-value storage.

## Features

- Append-only log storage
- In-memory index for fast lookups
- Thread-safe operations
- Data persistence
- Support for complex data types with dual serialization:
  - **Protocol Buffers** (normal mode) - Compact binary format for production
  - **JSON** (debug mode) - Human-readable format for development
- Tombstone-based deletion
- CLI and REST API interfaces

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

   # Install with CLI and server support
   uv pip install -e ".[server]"

   # Install development dependencies (includes server)
   uv pip install -e ".[dev]"
   ```

5. Run tests:
   ```bash
   pytest tests/ -v
   ```

## Development Setup

1. Install Protocol Buffers compiler:
   ```bash
   # On macOS
   brew install protobuf
   ```

2. After checking out the code, install the package in development mode:
   ```bash
   uv pip install -e .
   ```
   This will:
   - Generate the protobuf files
   - Install the package in editable mode
   - Make all dependencies available

3. For development with all tools:
   ```bash
   uv pip install -e ".[dev]"
   ```

4. To regenerate Protocol Buffers files:
   ```bash
   protoc --python_out=. --mypy_out=. src/pybitcask/proto/record.proto
   ```

## Data Formats

PyBitcask supports two serialization formats that can be switched at runtime:

### Protocol Buffers (Normal Mode)
- **Use Case**: Production environments
- **Benefits**:
  - Compact binary format (smaller file sizes)
  - Fast serialization/deserialization
  - Schema evolution support
  - Language-agnostic format
- **File Extension**: `.db` files contain binary protobuf data

### JSON (Debug Mode)
- **Use Case**: Development and debugging
- **Benefits**:
  - Human-readable format
  - Easy to inspect and debug
  - Standard format for web APIs
  - Simple text-based storage
- **File Extension**: `.db` files contain JSON text data

### Switching Modes

```bash
# Switch to debug mode (JSON)
pbc mode debug

# Switch to normal mode (Protocol Buffers)
pbc mode normal

# Check current mode
pbc mode show
```

**Note**: Data written in one mode cannot be read in the other mode. Clear the database when switching modes for existing data.

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

### Python API

```python
from pybitcask import Bitcask

# Normal mode (Protocol Buffers) - Production use
db = Bitcask("data", debug_mode=False)

# Debug mode (JSON) - Development use
db_debug = Bitcask("data", debug_mode=True)

# Store complex data types directly
sensor_data = {
    "temperature": 25.5,
    "humidity": 60,
    "timestamp": "2024-01-01T12:00:00Z",
    "location": {"lat": 37.7749, "lng": -122.4194}
}

db.put("sensor1:latest", sensor_data)
retrieved_data = db.get("sensor1:latest")
print(retrieved_data)  # Original dict structure preserved
```

### CLI Usage

```bash
# Install CLI dependencies
uv pip install -e ".[server]"

# Basic operations
pbc put user:123 '{"name": "Alice", "age": 30}'
pbc get user:123
pbc list
pbc delete user:123

# Switch between modes
pbc mode debug    # Human-readable JSON format
pbc mode normal   # Compact Protocol Buffers format

# Start REST API server
pbc server start --port 8000
```

### REST API Usage

```bash
# Store data
curl -X POST "http://localhost:8000/put" \
     -H "Content-Type: application/json" \
     -d '{"key": "user:123", "value": {"name": "Alice", "age": 30}}'

# Retrieve data
curl "http://localhost:8000/get/user:123"

# List all keys
curl "http://localhost:8000/keys"
```

### IoT Data Store Example

```python
from pybitcask import Bitcask
import time

class IoTDataStore:
    def __init__(self, data_dir, debug_mode=False):
        self.db = Bitcask(data_dir, debug_mode=debug_mode)

    def store_sensor_data(self, device_id, sensor_data):
        # Create a composite key with timestamp
        key = f"{device_id}:{int(time.time())}"
        # No need for manual JSON serialization - handled automatically
        self.db.put(key, sensor_data)

    def get_device_history(self, device_id, start_time, end_time):
        results = []
        for key in self.db.list_keys():
            if key.startswith(device_id):
                timestamp = int(key.split(':')[1])
                if start_time <= timestamp <= end_time:
                    results.append(self.db.get(key))
        return results

# Usage
store = IoTDataStore("iot_data", debug_mode=True)  # JSON for development
store.store_sensor_data("sensor1", {
    "temperature": 25.5,
    "humidity": 60,
    "battery": 85.2
})
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
   - Add TTL (Time To Live) support

2. **Scalability**
   - Add built-in sharding support
   - Implement replication
   - Add distributed coordination
   - Implement horizontal scaling

3. **Performance**
   - ✅ **Batch operation support** (implemented via REST API)
   - Implement async operations
   - Add caching layer
   - Optimize memory usage

4. **Interfaces**
   - ✅ **CLI interface** (implemented)
   - ✅ **REST API server** (implemented)
   - Add GraphQL API
   - Add gRPC interface

5. **Monitoring**
   - ✅ **Health checks** (implemented in server)
   - Add metrics collection
   - Add performance monitoring
   - Add logging improvements

# Python Bitcask Implementation

This is a Python implementation of the Bitcask storage engine, which provides an efficient and reliable way to store and retrieve key-value pairs.

## Features

- Append-only log storage
- In-memory index for fast lookups
- Thread-safe operations
- Data persistence
- Support for complex data types (via JSON serialization)
- Tombstone-based deletion

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

### Performance Considerations

- Write operations are O(1) due to append-only nature
- Read operations are O(1) due to in-memory index
- Memory usage grows with the number of unique keys
- Disk space usage grows with the number of operations (including updates and deletes)

## Limitations

1. No built-in compaction mechanism
2. No range queries support
3. All data must be JSON-serializable
4. Memory usage proportional to the number of keys

## Future Improvements

1. Implement compaction to reduce disk space usage
2. Add support for range queries
3. Implement data compression
4. Add support for batch operations
5. Implement replication for distributed systems 
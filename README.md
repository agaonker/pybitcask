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
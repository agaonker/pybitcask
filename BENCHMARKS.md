# Performance Benchmarks

## Benchmark Configuration

- Data sizes: 1,000, 10,000, and 100,000 entries
- Value sizes: 100, 1,000, and 10,000 bytes
- Operations tested: Sequential Write, Sequential Read, Random Read, Batch Write, and Delete

## Results

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

## Key Observations

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

## Performance Characteristics

- **Scalability**: Performance remains stable as data size increases from 1K to 100K entries
- **Value Size Impact**: Operations with 10KB values take about 4-5x longer than with 100B values
- **Consistency**: Very consistent performance across operations, especially for deletes
- **Memory Efficiency**: In-memory index enables fast lookups without significant performance degradation

## Benchmark Environment

- OS: macOS 23.5.0
- Python: 3.11.0
- CPU: Apple Silicon
- Memory: 16GB
- Storage: SSD

## Running Benchmarks

To run the benchmarks:

```bash
# Run benchmarks
python benchmarks/benchmark.py

# Generate visualizations
python benchmarks/visualize.py
```

The visualization script will generate:
- Operation time plots with error bars
- Comparison plots between different operations
- Value size impact analysis
- A comprehensive benchmark report

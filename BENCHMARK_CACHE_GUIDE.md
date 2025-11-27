# Cache Performance Benchmark Guide

This guide explains how to use the benchmark tools to compare LRU cache performance against no-cache scenarios.

## Overview

The benchmark system measures two key metrics:
- **Latency**: Response time for individual queries (lower is better)
- **Throughput**: Number of queries processed per second (higher is better)

## Quick Start

### Run Full Benchmark

```bash
python benchmark_cache_performance.py
```

This will:
- Test with sample sizes: 20, 40, 60, 80 queries
- Compare WITH LRU cache vs WITHOUT cache
- Generate detailed performance reports
- Save results to `benchmark_results.json`

### Run Quick Test

For faster testing with smaller samples:

```bash
python benchmark_cache_quick.py
```

This runs a faster version with sample sizes: 10, 20, 30 queries.

## Understanding the Results

### Metrics Explained

#### Latency Metrics
- **Average Latency**: Mean response time across all queries
- **Median Latency**: Middle value (50th percentile)
- **P95 Latency**: 95th percentile (95% of queries are faster)
- **P99 Latency**: 99th percentile (99% of queries are faster)
- **Min/Max Latency**: Fastest and slowest query times
- **Std Dev**: Variability in response times

#### Throughput Metrics
- **Throughput**: Queries processed per second
- **Total Time**: Complete execution time for all queries
- **Time Saved**: Time reduction with caching enabled

#### Performance Metrics
- **Speedup Factor**: How many times faster cached queries are
- **Improvement %**: Percentage improvement over no-cache baseline

### Sample Output

```
================================================================================
Sample Size: 40 queries
================================================================================

📈 LATENCY METRICS
--------------------------------------------------------------------------------
Metric                    With LRU Cache       Without Cache        Improvement    
--------------------------------------------------------------------------------
Average Latency           2.145                5.234                59.0%
Median Latency            1.832                5.102                64.1%
P95 Latency               4.321                6.543                33.9%

⚡ THROUGHPUT METRICS
--------------------------------------------------------------------------------
Metric                    With LRU Cache       Without Cache        Improvement    
--------------------------------------------------------------------------------
Throughput (queries/sec)  0.466                0.191                143.9%
Total Time (seconds)      85.800               209.360              59.0%
Time Saved (seconds)      123.560

🎯 SPEEDUP FACTOR
--------------------------------------------------------------------------------
Average query with LRU cache is 2.44x faster
```

## Benchmark Configuration

### Modifying Sample Sizes

Edit the `sample_sizes` list in the script:

```python
# In benchmark_cache_performance.py
sample_sizes = [20, 40, 60, 80]  # Change these values
```

### Modifying Cache Size

Change the cache size parameter:

```python
lru_cache_manager = LRUDataManager(cache_size=128)  # Default is 128
```

### Adding Custom Test Questions

Edit the `base_questions` list:

```python
base_questions = [
    "Your custom question 1?",
    "Your custom question 2?",
    # Add more questions...
]
```

## Key Features

### 1. Realistic Workload Simulation

The benchmark simulates realistic query patterns by:
- Repeating questions (simulates common queries)
- Shuffling queries (simulates random access patterns)
- Including variety (tests cache eviction)

### 2. Cache Hit Rate Testing

The repeated questions test cache effectiveness:
- First query: Cache miss (full processing)
- Subsequent queries: Cache hit (instant retrieval)

### 3. Statistical Rigor

Multiple measurements provide:
- Mean and median for central tendency
- Standard deviation for variability
- Percentiles (P95, P99) for tail latency

## Interpreting Results

### What to Look For

#### Good Cache Performance
- ✅ 40-70% reduction in average latency
- ✅ 2-3x speedup factor
- ✅ Significant throughput improvement
- ✅ Lower P95/P99 latency

#### Poor Cache Performance
- ❌ <20% latency reduction
- ❌ <1.5x speedup
- ❌ High standard deviation
- ❌ Similar P95 latency with/without cache

### Common Patterns

#### Scenario 1: High Cache Hit Rate
```
Average Latency: 2.0s (with cache) vs 6.0s (without cache)
Speedup: 3.0x
```
**Analysis**: Cache is highly effective, queries are being reused.

#### Scenario 2: Low Cache Hit Rate
```
Average Latency: 5.5s (with cache) vs 6.0s (without cache)
Speedup: 1.09x
```
**Analysis**: Few cache hits, most queries are unique. Consider:
- Increasing cache size
- Analyzing query patterns
- Checking cache key generation

#### Scenario 3: Variable Performance
```
Average Latency: 3.0s, Std Dev: 2.5s
```
**Analysis**: High variability indicates mixed cache hits/misses.

## Advanced Usage

### Custom Benchmark Scenarios

Create your own benchmark by using the `run_benchmark()` function:

```python
from benchmark_cache_performance import run_benchmark

# Define your questions
questions = ["question1", "question2", ...]

# Run with custom cache
result = run_benchmark(
    questions=questions,
    conn=conn,
    prune_module=prune_module,
    cache_manager=your_cache_manager,
    # ... other parameters
    benchmark_name="My Custom Test",
)

# Get statistics
stats = result.compute_stats()
print(stats)
```

### Comparing Multiple Cache Strategies

Test different cache sizes or strategies:

```python
cache_sizes = [32, 64, 128, 256]

for size in cache_sizes:
    cache_manager = LRUDataManager(cache_size=size)
    result = run_benchmark(...)
    # Compare results
```

## Output Files

### benchmark_results.json

Contains structured results for further analysis:

```json
{
  "timestamp": "2024-11-26 10:30:00",
  "results": [
    {
      "name": "With LRU Cache (n=40)",
      "sample_size": 40,
      "avg_latency": 2.145,
      "throughput": 0.466,
      ...
    }
  ]
}
```

Use this file for:
- Plotting graphs
- Historical comparison
- Automated analysis

## Best Practices

### 1. Run Multiple Times

For consistent results, run benchmarks multiple times:

```bash
for i in {1..5}; do
    python benchmark_cache_performance.py
    sleep 60
done
```

### 2. Consistent Environment

Ensure:
- No other heavy processes running
- Stable network connection (for LLM API calls)
- Sufficient system resources

### 3. Warm-up Period

The first few queries may be slower due to:
- Cold start effects
- Network connection initialization
- Model loading

### 4. Sample Size Selection

- **Small (10-20)**: Quick tests, less accurate
- **Medium (40-60)**: Good balance of speed/accuracy
- **Large (100+)**: Most accurate, takes longer

## Troubleshooting

### Issue: Very slow execution

**Solution**: 
- Reduce sample sizes
- Use `benchmark_cache_quick.py` instead
- Check network connection to LLM API

### Issue: No performance improvement

**Solution**:
- Verify cache is enabled
- Check if questions are being repeated
- Review cache size (may be too small)

### Issue: High variability in results

**Solution**:
- Run multiple iterations
- Increase sample size
- Check for network instability

## Cost Considerations

Each query makes LLM API calls. Benchmark costs:
- Small test (30 queries): ~$0.06
- Medium test (160 queries): ~$0.32
- Large test (500 queries): ~$1.00

Estimates based on $0.002 per query (actual costs may vary).

## Further Reading

- [CACHE_STRATEGIES.md](CACHE_STRATEGIES.md) - Cache design patterns
- [CACHE_INTEGRATION.md](CACHE_INTEGRATION.md) - Implementation details
- [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md) - General benchmarking guide


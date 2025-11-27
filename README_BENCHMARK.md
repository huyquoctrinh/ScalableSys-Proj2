# Cache Performance Benchmark Suite

A comprehensive benchmarking suite to measure and compare the performance of the Graph RAG system with and without LRU caching.

## 🚀 Quick Start

### 1. Run Quick Benchmark (Recommended for First Time)

```bash
python benchmark_cache_quick.py
```

This runs a fast benchmark with smaller sample sizes (10, 20, 30 queries) - takes ~5-10 minutes.

### 2. Run Full Benchmark

```bash
python benchmark_cache_performance.py
```

This runs a comprehensive benchmark with larger sample sizes (20, 40, 60, 80 queries) - takes ~15-30 minutes.

### 3. Visualize Results

```bash
python visualize_benchmark.py
```

This generates charts and graphs from the benchmark results.

## 📊 What Gets Measured

### Latency Metrics
- **Average Latency**: Mean query response time
- **Median Latency**: 50th percentile response time
- **P95 Latency**: 95th percentile (95% of queries are faster)
- **P99 Latency**: 99th percentile (99% of queries are faster)
- **Min/Max**: Fastest and slowest queries
- **Standard Deviation**: Response time variability

### Throughput Metrics
- **Queries per Second**: Number of queries processed per second
- **Total Time**: Complete execution time for all queries
- **Time Saved**: Time reduction with caching

### Performance Metrics
- **Speedup Factor**: How many times faster cached queries are
- **Improvement Percentage**: % improvement in latency/throughput

## 📁 Output Files

After running benchmarks, you'll get:

### JSON Results
- `benchmark_results.json` - Full benchmark data
- `quick_benchmark_results.json` - Quick benchmark data

### Visualization Charts (after running visualize_benchmark.py)
- `latency_comparison.png` - Latency metrics comparison
- `throughput_comparison.png` - Throughput metrics comparison
- `speedup_factor.png` - Cache speedup across sample sizes
- `time_comparison.png` - Total time and time saved
- `performance_dashboard.png` - Comprehensive summary dashboard

## 🔧 Configuration

### Modify Sample Sizes

Edit the `sample_sizes` list in the benchmark scripts:

```python
# In benchmark_cache_performance.py
sample_sizes = [20, 40, 60, 80]  # Change these

# In benchmark_cache_quick.py
sample_sizes = [10, 20, 30]  # Change these
```

### Modify Cache Size

Change the cache size parameter:

```python
lru_cache_manager = LRUDataManager(cache_size=128)  # Change 128 to your size
```

### Add Custom Questions

Edit the `base_questions` list:

```python
base_questions = [
    "Your custom question 1?",
    "Your custom question 2?",
    # Add more...
]
```

## 📈 Example Output

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

💰 ESTIMATED COST SAVINGS
--------------------------------------------------------------------------------
Estimated cost saved: $0.2471
```

## 🎯 Understanding Results

### Good Cache Performance
- ✅ 40-70% reduction in average latency
- ✅ 2-3x or higher speedup factor
- ✅ Significant throughput improvement
- ✅ Lower variance in response times

### Poor Cache Performance
- ❌ <20% latency reduction
- ❌ <1.5x speedup
- ❌ Similar P95 latency with/without cache
- ❌ High standard deviation

## 🔍 Detailed Guides

- [BENCHMARK_CACHE_GUIDE.md](BENCHMARK_CACHE_GUIDE.md) - Comprehensive guide
- [CACHE_STRATEGIES.md](CACHE_STRATEGIES.md) - Cache design patterns
- [CACHE_INTEGRATION.md](CACHE_INTEGRATION.md) - Implementation details

## 💡 Tips for Best Results

1. **Run Multiple Times**: Results can vary due to network latency
2. **Stable Environment**: Close other applications, stable internet
3. **Appropriate Sample Size**: Start small (10-20), then scale up
4. **Understand Your Workload**: Adjust questions to match real usage

## 🛠️ Troubleshooting

### Benchmark runs very slowly
- Try `benchmark_cache_quick.py` with smaller sample sizes
- Check your internet connection
- Verify LLM API is responding properly

### No performance improvement
- Verify cache is enabled
- Check if questions are being repeated (cache needs repeats to show benefit)
- Review cache size - may be too small

### Visualization fails
- Install matplotlib: `pip install matplotlib`
- Ensure benchmark results file exists
- Check for any errors in the console

## 📦 Dependencies

```bash
# Core dependencies (already in pyproject.toml)
kuzu
dspy-ai
python-dotenv

# Visualization (add if not present)
matplotlib
numpy
```

## 🚀 Complete Workflow

```bash
# 1. Run quick benchmark
python benchmark_cache_quick.py

# 2. Review results (printed to console)

# 3. Generate visualizations
python visualize_benchmark.py

# 4. Run full benchmark for detailed analysis
python benchmark_cache_performance.py

# 5. Generate final visualizations
python visualize_benchmark.py

# 6. Review all generated PNG files
```

## 📊 Sample Benchmark Results

Typical results you might see:

| Sample Size | Avg Latency (LRU) | Avg Latency (No Cache) | Speedup |
|-------------|-------------------|------------------------|---------|
| 20          | 2.3s              | 5.1s                   | 2.2x    |
| 40          | 2.1s              | 5.2s                   | 2.5x    |
| 60          | 2.0s              | 5.3s                   | 2.7x    |
| 80          | 1.9s              | 5.2s                   | 2.7x    |

Notice how:
- Larger samples show better cache benefits (more repeats)
- Speedup increases with sample size
- Average latency with cache decreases (more cache hits)

## 🎓 What You Learn

From these benchmarks, you'll understand:

1. **Cache Effectiveness**: How much faster your system becomes with caching
2. **Scaling Behavior**: How performance changes with load
3. **Cost Savings**: Reduced LLM API calls = lower costs
4. **Optimization Opportunities**: Where to focus improvement efforts

## 🔗 Related Files

- `graph_rag_workflow.py` - Main application with built-in benchmarking
- `cache_method/` - LRU cache implementation
- `test/test_lru_cache.py` - Unit tests for cache

## 📝 Notes

- Benchmark results depend on many factors: network speed, LLM API response time, query complexity
- Results are most meaningful when comparing relative performance (with vs without cache)
- Actual production performance may vary based on query distribution and cache hit rates

## 🤝 Contributing

To add new benchmark scenarios:

1. Create a new test questions set
2. Modify sample sizes as needed
3. Run benchmarks
4. Compare results
5. Share findings!

---

For detailed documentation, see [BENCHMARK_CACHE_GUIDE.md](BENCHMARK_CACHE_GUIDE.md)


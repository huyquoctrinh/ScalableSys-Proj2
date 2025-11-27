# Benchmark Cache Performance - Updated

## What's New

The benchmark has been updated to properly compare **LRU cache vs no cache** with the new caching workflow that stores context instead of final answers.

## Key Changes

### 1. **Cache Hit/Miss Tracking**
The benchmark now tracks:
- Number of cache hits
- Number of cache misses  
- Cache hit rate percentage
- Performance per cache hit vs miss

### 1.5. **Token Throughput Measurement**
The benchmark now measures:
- **Tokens generated** per query
- **Tokens per second** throughput (more accurate than queries/sec)
- **Total tokens** across all queries
- **Average tokens per query**

This provides better insight into actual LLM performance!

### 2. **Proper No-Cache Comparison**
The no-cache benchmark now:
- **Disables caching entirely** (`is_cache_enabled=False`)
- Runs full pipeline for every query
- Shows true performance without any caching benefit
- Uses `NoCacheManager` as a dummy (always returns None)

### 3. **Enhanced Reporting**
New metrics in the comparison report:
- Cache hit rate for each benchmark
- Cost calculations considering partial cost for cache hits
- Real-time progress with cache hit tracking

## How It Works

### With LRU Cache Enabled
```python
# First query (cache miss)
Question → Prune Schema → Generate Query → Execute → Cache Context → Generate Answer
Time: ~8-10 seconds

# Same question again (cache hit)
Question → Prune Schema → Retrieve Context from Cache → Generate Answer
Time: ~0.5-1 second
```

### Without Cache (Disabled)
```python
# Every query (no cache)
Question → Prune Schema → Generate Query → Execute → Generate Answer
Time: ~8-10 seconds (every time)
```

## Running the Benchmark

```bash
python benchmark_cache_performance.py
```

### What You'll See

```
============================================================
Testing with sample size: 20 queries
============================================================
Generated 20 test queries (with repetitions for cache testing)

🔄 Running benchmark: With LRU Cache (n=20)
   Processing 20 queries...
   Cache ENABLED
   Progress: 10/20 queries | Cache hits: 5 (50.0%)
   ✅ Completed 20 queries
   📊 Final cache hit rate: 10/20 (50.0%)

🔄 Running benchmark: Without Cache (n=20)
   Processing 20 queries...
   Cache DISABLED
   Progress: 10/20 queries | Cache hits: 0 (0.0%)
   ✅ Completed 20 queries
   📊 Final cache hit rate: 0/20 (0.0%)
```

## Understanding the Results

### Latency Metrics
```
Metric                    With LRU Cache       Without Cache        Improvement
--------------------------------------------------------------------------------
Average Latency          1.234                8.567                85.6%
Median Latency           0.876                8.432                89.6%
P95 Latency              2.456                9.234                73.4%
```

**Interpretation:**
- With cache: Mix of cache hits (~0.8s) and misses (~8s)
- Without cache: Every query takes full time (~8-10s)
- Improvement shows percentage reduction in latency

### Cache Statistics
```
Metric                    With LRU Cache       Without Cache
------------------------------------------------------------
Cache Hits               10                   0
Cache Misses             10                   20
Cache Hit Rate           50.0%                0.0%
```

**Why no-cache has 0% hit rate:**
- Cache is disabled (`is_cache_enabled=False`)
- All queries are treated as cache misses
- No context is stored or retrieved

### Cost Analysis
```
Total cost (with cache): $0.0220
Total cost (no cache): $0.0400
Cost saved: $0.0180 (45.0%)
```

**Cost breakdown:**
- **Cache miss**: Full LLM cost (~$0.002 per query)
- **Cache hit**: Answer gen only (~$0.0002 per query)
- **No cache**: Always full cost (~$0.002 per query)

With 50% hit rate:
- 10 misses × $0.002 = $0.020
- 10 hits × $0.0002 = $0.002
- **Total**: $0.022 (vs $0.040 without cache)

## Sample Sizes

The benchmark tests different sample sizes by default:
- **20 queries**: Quick test
- **40 queries**: Medium test
- **60 queries**: Larger test
- **80 queries**: Comprehensive test

### Why Multiple Sample Sizes?

1. **Cache Warmup**: Larger samples show better hit rates
2. **Statistical Significance**: More data = more reliable metrics
3. **Real-world Simulation**: Different workload patterns
4. **Performance Trends**: See how cache scales

## Expected Performance

### Typical Results (50% Hit Rate)

| Metric | With Cache | Without Cache | Improvement |
|--------|-----------|---------------|-------------|
| Avg Latency | 4.5s | 8.5s | **47%** |
| Throughput | 0.22 q/s | 0.12 q/s | **83%** |
| Total Time (20q) | 90s | 170s | **47%** |
| Cost Saved | - | - | **45%** |

### Why Not 90%+ Improvement?

With the new caching approach:
- **Old**: Cached final answer = no LLM call on hit
- **New**: Cached context = still need answer generation (~0.5s)

**Trade-off:**
- ❌ Slightly slower cache hits (0.8s vs 0.01s)
- ✅ Much more flexible (can change answer generation)
- ✅ Still saves 80-90% of processing time
- ✅ Better for development and iteration

## Customization

### Adjust Cache Size
```python
# In main() function, line ~393
lru_cache_manager = LRUDataManager(cache_size=256)  # Increase for more caching
```

### Change Sample Sizes
```python
# In main() function, line ~350
sample_sizes = [10, 20, 30, 50, 100]  # Customize test sizes
```

### Add More Questions
```python
# In main() function, line ~336
base_questions = [
    "Your question here",
    "Another question",
    # Add more...
]
```

### Adjust Repeat Factor
```python
# In main() function, line ~367
repeat_factor = (sample_size // len(base_questions)) + 2  # More repetitions = higher hit rate
```

## Visualizing Results

The benchmark saves results to `benchmark_results.json`. You can use `visualize_benchmark.py` to create charts:

```bash
python visualize_benchmark.py
```

This creates:
- `latency_comparison.png` - Average latency comparison
- `throughput_comparison.png` - Queries per second
- `speedup_factor.png` - Performance multiplier
- `time_comparison.png` - Total time comparison

## Troubleshooting

### Issue: Cache hit rate is 0% for both benchmarks

**Cause:** Questions are not being repeated or cache key is changing

**Solution:**
- Check `generate_test_questions()` is creating repetitions
- Verify schema pruning is consistent
- Check cache key generation

### Issue: No difference between benchmarks

**Cause:** Cache might not be working or both using same manager

**Solution:**
- Verify `is_cache_enabled` flag is set correctly
- Check `NoCacheManager` returns None
- Review process_question_benchmark logic

### Issue: Benchmark runs very slow

**Cause:** LLM API calls are expensive

**Solution:**
- Reduce sample sizes temporarily
- Use smaller repeat_factor
- Check API rate limits

## Best Practices

1. **Start Small**: Test with 10-20 queries first
2. **Check Logs**: Review `graph_rag_detailed.log` for issues
3. **Vary Questions**: Mix of repeated and unique questions
4. **Monitor API Costs**: Benchmarks make many LLM calls
5. **Save Results**: Keep `benchmark_results.json` for comparison

## Conclusion

The updated benchmark provides accurate comparison between:
- ✅ **LRU Cache**: Fast context retrieval + answer generation
- ✅ **No Cache**: Full pipeline every time
- ✅ **Realistic Performance**: Shows actual production behavior
- ✅ **Detailed Metrics**: Latency, throughput, cost, hit rates

Use this to:
- Validate cache performance
- Tune cache size
- Justify caching infrastructure
- Optimize query patterns

---
*Updated: November 27, 2025*


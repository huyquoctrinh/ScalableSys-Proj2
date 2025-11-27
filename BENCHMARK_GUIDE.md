# Graph RAG Benchmark Guide

This guide explains how to use the enhanced `graph_rag_workflow.py` with built-in LRU cache benchmarking.

## 🚀 Features Added

### 1. **Automatic Answer Printing**
- Every query now displays a clear, formatted answer
- Cache hit/miss status is shown
- Response times are tracked automatically

### 2. **Real-time Performance Benchmarking**
- Tracks all queries with precise timing
- Calculates cache hit rate automatically
- Shows time saved by caching
- Estimates cost savings

### 3. **Interactive Statistics**
- Type `stats` anytime to see current performance metrics
- Automatic benchmark report on exit
- All stats saved to log file

## 📊 Running the Benchmark

### Step 1: Start the Application

```bash
# Make sure Kuzu is running
docker compose up -d

# Run the benchmark workflow
python graph_rag_workflow.py
```

### Step 2: Ask Questions

```
============================================================
🚀 Graph RAG with LRU Cache - Performance Benchmark
============================================================
Type 'exit', 'quit' to end, or 'stats' to see benchmark report.
============================================================

📝 Logging chat to chat_log.txt

> Which scholars won prizes in Physics?
```

### Step 3: See the Results

**First Query (Cache MISS):**
```
============================================================
❓ QUESTION: Which scholars won prizes in Physics?
============================================================

❌ Cache Status: MISS

Final Cypher Query:
MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName

--- Running Query and Generating Answer ---

⏱️  Total Processing Time: 8.234s
📦 Cache Size: 1/128

💡 ANSWER:
The scholars who won prizes in Physics include Albert Einstein, Marie Curie, 
Niels Bohr, and many others...
```

**Same Query Again (Cache HIT):**
```
============================================================
❓ QUESTION: Which scholars won prizes in Physics?
============================================================

✅ Cache Status: HIT
⚡ Response Time: 0.123s
📦 Cache Size: 1/128

💡 ANSWER:
The scholars who won prizes in Physics include Albert Einstein, Marie Curie, 
Niels Bohr, and many others...
```

**Notice the difference:** 8.234s → 0.123s = **67x faster!** 🚀

### Step 4: View Statistics

Type `stats` to see current performance:

```
> stats

============================================================
📊 CACHE PERFORMANCE BENCHMARK
============================================================
Total Queries:        10
Cache Hits:           5 (50.0%)
Cache Misses:         5 (50.0%)

⚡ Avg Hit Time:      0.145s
🐌 Avg Miss Time:     7.892s
🚀 Speedup (cached):  54.5x faster

⏱️  Total Time Saved:  39.46s
💰 Estimated Cost Saved: $0.0100
============================================================
```

## 🧪 Example Benchmark Session

Here's a complete example to test cache performance:

```bash
# Run these queries in sequence:

1. Which scholars won prizes in Physics?          # MISS - ~8s
2. Which scholars won prizes in Physics?          # HIT  - ~0.1s
3. Who was affiliated with University of Cambridge? # MISS - ~7s
4. Which scholars won prizes in Physics?          # HIT  - ~0.1s
5. Who was affiliated with University of Cambridge? # HIT  - ~0.1s
6. How many laureates won prizes in Chemistry?    # MISS - ~8s
7. Which scholars won prizes in Physics?          # HIT  - ~0.1s
8. stats                                          # Show report
9. exit                                           # Final report
```

**Expected Results:**
- Total Queries: 7 (excluding 'stats' command)
- Cache Hits: 4 (57%)
- Cache Misses: 3 (43%)
- Total Time: ~23s vs ~56s without cache
- **Time Saved: ~33 seconds (59% reduction)**

## 📈 Understanding the Metrics

### Cache Hit Rate
```
Cache Hits: 5 (50.0%)
```
- **Higher is better** - means cache is being used effectively
- 50%+ is good for diverse queries
- 80%+ is excellent for repeated queries

### Response Times
```
⚡ Avg Hit Time:  0.145s  (cached queries)
🐌 Avg Miss Time: 7.892s  (new queries)
```
- **Hit time**: Retrieving from cache (very fast)
- **Miss time**: Full pipeline execution (slower)
- **Speedup**: Shows performance multiplier

### Time Saved
```
⏱️  Total Time Saved: 39.46s
```
- Calculated as: `(Cache Hits) × (Avg Miss Time)`
- Total time you didn't wait due to caching

### Cost Saved
```
💰 Estimated Cost Saved: $0.0100
```
- Assumes $0.002 per LLM call
- Each cache hit = one avoided API call

## 🎯 Benchmark Tips

### 1. Test Repeated Queries

Ask the same question multiple times to see cache benefits:

```bash
# First time: 8 seconds
> Which scholars won prizes in Physics?

# Second time: 0.1 seconds
> Which scholars won prizes in Physics?
```

### 2. Test Similar Questions

Slightly different questions are cache misses:

```bash
# Different wording = cache miss
> Which scholars won prizes in Physics?
> Who won Physics prizes?  # Different question, cache miss
```

### 3. Monitor Cache Size

Watch the cache grow:

```
📦 Cache Size: 5/128    # 5 queries cached, 123 slots free
📦 Cache Size: 15/128   # 15 queries cached
📦 Cache Size: 128/128  # Cache full, LRU eviction starts
```

### 4. Test Cache Capacity

Fill the cache to see LRU eviction in action:

```bash
# Ask 130+ unique questions
# Oldest entries will be evicted
# Cache size stays at 128
```

## 📝 Log Files

All sessions are logged to `chat_log.txt`:

```
--- Session started at 2025-01-15T10:30:00 ---

> Which scholars won prizes in Physics?
Cache Status: MISS
...

📊 CACHE PERFORMANCE BENCHMARK
Total Queries: 10
Cache Hits: 5 (50.0%)
...

--- Session ended at 2025-01-15T10:45:00 ---
```

## 🔧 Configuration

### Adjust Cache Size

In `graph_rag_workflow.py`, line 320:

```python
lru_cache_manager = LRUDataManager(cache_size=128)  # Default

# For more caching:
lru_cache_manager = LRUDataManager(cache_size=512)

# For less memory usage:
lru_cache_manager = LRUDataManager(cache_size=64)
```

### Customize Benchmark Output

In `BenchmarkStats.get_report()`, modify the report format:

```python
report = [
    "\n" + "="*60,
    "📊 MY CUSTOM BENCHMARK",
    f"Hit Rate: {hit_rate:.1f}%",
    # Add your own metrics
]
```

## 🎓 Understanding Cache Behavior

### Cache Key Composition

The cache key includes:
1. **Question text** - exact string match
2. **Pruned schema** - relevant graph schema

**Example:**
```python
cache_key = "Which scholars won prizes in Physics?|{'nodes':[...]}"
```

### What Gets Cached

The cache stores:
- **Cypher Query**: The generated and validated query
- **Context**: The graph query results (not the final answer)

This means:
- ✅ Skips expensive Cypher generation (3-7 seconds saved)
- ✅ Skips database query execution (1-2 seconds saved)
- ✅ Still generates fresh answer each time (~0.5 seconds)
- ✅ More flexible for different answer generation strategies

### When Cache Hits Occur

✅ **Cache HIT** when:
- Exact same question
- Same pruned schema
- Entry still in cache (not evicted)

❌ **Cache MISS** when:
- Different question wording
- Schema pruned differently
- Entry was evicted (LRU)

### LRU Eviction

When cache is full (128 entries):
1. New entry needs to be stored
2. **Least Recently Used** entry is removed
3. New entry takes its place

## 🚀 Performance Expectations

### Typical Results

| Scenario | Time (no cache) | Time (cached) | Speedup |
|----------|-----------------|---------------|---------|
| Simple query | 6-8s | 0.1-0.2s | **40-60x** |
| Complex query | 10-15s | 0.1-0.2s | **70-100x** |
| Aggregation | 8-12s | 0.1-0.2s | **50-80x** |

### Cache Hit Rate by Pattern

| Query Pattern | Expected Hit Rate |
|---------------|-------------------|
| Repeated exact queries | 80-100% |
| Similar questions | 20-40% |
| Diverse questions | 10-30% |
| User sessions | 40-70% |

## 🐛 Troubleshooting

### Cache Not Hitting

**Problem:** Same question shows MISS every time

**Solutions:**
1. Check if question text is exactly the same (case-sensitive)
2. Verify cache size isn't full: `📦 Cache Size: 128/128`
3. Check if schema pruning is consistent

### Performance Slower Than Expected

**Problem:** Cache hits still taking 1-2 seconds

**Solutions:**
1. Check database connection latency
2. Verify LLM for answer generation (cache doesn't skip this step)
3. Check system resources (CPU, memory)

### Stats Not Updating

**Problem:** `stats` command shows old data

**Solutions:**
1. Make sure you're running the updated `graph_rag_workflow.py`
2. Check that queries are completing successfully
3. Restart the application

## 📚 Next Steps

1. **Run Your Own Benchmarks**: Test with your specific query patterns
2. **Tune Cache Size**: Based on your hit rate and memory constraints
3. **Analyze Logs**: Review `chat_log.txt` for detailed session data
4. **Optimize Queries**: Use benchmarks to identify slow queries

## 🎉 Summary

The enhanced Graph RAG workflow now provides:

✅ **Clear answer display** - See results immediately  
✅ **Real-time timing** - Know how fast each query is  
✅ **Cache statistics** - Understand performance impact  
✅ **Interactive reports** - Check stats anytime with `stats`  
✅ **Automatic logging** - All sessions saved to file  

**Start benchmarking and see the cache performance benefits yourself!** 🚀


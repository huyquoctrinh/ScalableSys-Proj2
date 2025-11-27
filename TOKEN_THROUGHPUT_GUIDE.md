# Token Throughput Measurement Guide

## Overview

The benchmark now measures throughput in **tokens inferred per second** in addition to queries per second. This provides a more accurate measure of LLM performance and system efficiency.

---

## Why Token Throughput Matters

### Query Throughput Limitation
```
Query 1: "Who won Physics?" → 50 token answer
Query 2: "List all Nobel laureates from 1901 to 2023" → 500 token answer

Both count as "1 query" but vastly different computational costs!
```

### Token Throughput Benefits
- ✅ **Accurate performance measurement**: Reflects actual LLM inference work
- ✅ **Cost estimation**: LLM APIs charge by tokens
- ✅ **Capacity planning**: Better predict system limits
- ✅ **Fair comparison**: Normalize for answer length variability

---

## How It Works

### Token Counting

The benchmark uses **tiktoken** (OpenAI's tokenizer) when available:

```python
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4/3.5 encoding
tokens = len(encoding.encode(text))
```

**Fallback**: If tiktoken is not installed, uses a heuristic (~4 chars per token)

### Installation (Optional)

For accurate token counting:
```bash
pip install tiktoken
```

Without tiktoken, the benchmark still works using the character-based heuristic.

---

## Metrics Tracked

### Per Query
- **Latency**: Time to process query (seconds)
- **Tokens**: Number of tokens in the generated answer
- **Cache Status**: Hit or miss

### Aggregate
- **Total Tokens**: Sum of all tokens generated
- **Avg Tokens/Query**: Average answer length
- **Throughput (queries/sec)**: Traditional metric
- **Throughput (tokens/sec)**: New metric for LLM performance

---

## Example Output

### During Benchmark
```
🔄 Running benchmark: With LRU Cache (n=20)
   Processing 20 queries...
   Cache ENABLED
   Progress: 10/20 queries | Cache hits: 5 (50.0%) | Tokens: 1,234
   ✅ Completed 20 queries
   📊 Final cache hit rate: 10/20 (50.0%)
   📝 Total tokens generated: 2,456
```

### In Comparison Report
```
⚡ THROUGHPUT METRICS
--------------------------------------------------------------------------------
Metric                    With LRU Cache       Without Cache        Improvement
--------------------------------------------------------------------------------
Throughput (queries/sec)  0.234                0.125                87.2%
Throughput (tokens/sec)   58.5                 31.2                 87.5%
Total Tokens Generated    2,456                2,498                -
Avg Tokens per Query      122.8                124.9                -
```

---

## Interpreting Results

### Token Throughput (tokens/sec)

**High throughput (>50 tokens/sec):**
- Efficient system
- Good cache utilization
- Fast LLM inference

**Medium throughput (20-50 tokens/sec):**
- Typical for complex queries
- Cache helping moderately
- Normal performance

**Low throughput (<20 tokens/sec):**
- System bottleneck
- Poor cache hit rate
- May need optimization

### Example Calculation

```
Benchmark Run:
- 20 queries processed
- 90 seconds total time
- 2,456 tokens generated

Token Throughput = 2,456 tokens / 90 seconds = 27.3 tokens/sec
Query Throughput = 20 queries / 90 seconds = 0.22 queries/sec
```

---

## Comparison: With vs Without Cache

### Typical Results (50% hit rate)

| Metric | With Cache | Without Cache | Improvement |
|--------|-----------|---------------|-------------|
| **Queries/sec** | 0.22 | 0.12 | **83%** |
| **Tokens/sec** | 55 | 30 | **83%** |
| **Avg Latency** | 4.5s | 8.0s | **44%** |
| **Total Tokens** | 2,456 | 2,498 | Similar |

**Key Insight**: Both metrics show similar improvement percentages because:
- Cache reduces processing time equally
- Answer length relatively consistent across queries
- Token throughput validates query throughput gains

---

## Cache Impact on Token Generation

### Cache Hit
```
Time: 0.8s
Tokens: 120
Token Throughput: 150 tokens/sec
```

### Cache Miss
```
Time: 8.0s
Tokens: 125
Token Throughput: 15.6 tokens/sec
```

**Cache benefit**: 10x faster token generation (same LLM, less overhead)

---

## Advanced Analysis

### Token Efficiency by Cache Status

The benchmark can show:
- **Cache Hit Token Rate**: Tokens/sec for cache hits only
- **Cache Miss Token Rate**: Tokens/sec for cache misses only
- **Overall Token Rate**: Combined average

This helps identify:
- Is the LLM inference the bottleneck?
- How much time is spent in query generation vs answer generation?
- What's the true speedup from caching?

---

## Cost Analysis with Tokens

### LLM Pricing (example)
```
- Input tokens: $0.03 / 1K tokens
- Output tokens: $0.06 / 1K tokens
```

### Cost Calculation
```python
# Cache miss (generates query + answer)
input_tokens = 500  # Schema, exemplars, question
output_tokens = 150  # Cypher query + answer
cost = (500 * 0.03 + 150 * 0.06) / 1000 = $0.024

# Cache hit (only generates answer)
input_tokens = 300  # Schema, cached context, question
output_tokens = 120  # Answer only
cost = (300 * 0.03 + 120 * 0.06) / 1000 = $0.016

Savings per cache hit: $0.008 (33%)
```

---

## Optimization Strategies

### Improve Token Throughput

1. **Increase Cache Hit Rate**
   - Larger cache size
   - Better cache key design
   - Pre-warm cache with common queries

2. **Reduce Answer Generation Time**
   - Use faster LLM models
   - Optimize prompts for conciseness
   - Use streaming responses

3. **Optimize Query Generation**
   - Better exemplar selection
   - Fewer refinement iterations
   - Simpler post-processing

### Target Benchmarks

| System | Tokens/sec | Use Case |
|--------|-----------|----------|
| **Development** | 20-30 | Iterating, testing |
| **Production** | 30-50 | Live queries, moderate load |
| **High Performance** | 50-100+ | Heavy caching, optimized |

---

## Monitoring in Production

### Key Metrics to Track

1. **Token Throughput Trend**
   ```python
   tokens_per_second = total_tokens / elapsed_time
   ```

2. **Cost per Token**
   ```python
   cost_per_token = total_cost / total_tokens
   ```

3. **Token Efficiency**
   ```python
   cache_hit_token_rate = tokens_generated_on_hits / time_for_hits
   cache_miss_token_rate = tokens_generated_on_misses / time_for_misses
   efficiency_gain = cache_hit_token_rate / cache_miss_token_rate
   ```

---

## Troubleshooting

### Token Count Seems Wrong

**Problem**: Token counts don't match expected values

**Solutions**:
1. Install tiktoken for accurate counting:
   ```bash
   pip install tiktoken
   ```

2. Verify encoding matches your LLM:
   ```python
   # For GPT-4/3.5-turbo
   encoding = tiktoken.get_encoding("cl100k_base")
   
   # For older models
   encoding = tiktoken.get_encoding("p50k_base")
   ```

3. Check text content:
   ```python
   print(f"Answer: {final_answer}")
   print(f"Tokens: {count_tokens(final_answer)}")
   ```

### Low Token Throughput

**Problem**: Less than 20 tokens/sec consistently

**Diagnose**:
1. Check cache hit rate (should be >30%)
2. Profile LLM API latency
3. Check network latency to LLM provider
4. Review query complexity

**Fix**:
- Increase cache size
- Use faster LLM endpoint
- Reduce prompt complexity
- Enable response streaming

---

## Example: Production Monitoring

### Setup Monitoring

```python
from dataclasses import dataclass
from time import time

@dataclass
class TokenMetrics:
    start_time: float = time()
    total_queries: int = 0
    total_tokens: int = 0
    
    def record_query(self, tokens: int):
        self.total_queries += 1
        self.total_tokens += tokens
    
    def get_throughput(self) -> dict:
        elapsed = time() - self.start_time
        return {
            "queries_per_sec": self.total_queries / elapsed,
            "tokens_per_sec": self.total_tokens / elapsed,
            "avg_tokens_per_query": self.total_tokens / self.total_queries
        }

# Usage
metrics = TokenMetrics()

for query in queries:
    answer = process(query)
    tokens = count_tokens(answer)
    metrics.record_query(tokens)

print(metrics.get_throughput())
```

---

## Summary

### What Changed
- ✅ Benchmark now tracks **tokens generated** per query
- ✅ Calculates **tokens/second throughput**
- ✅ Reports **total tokens** and **average tokens per query**
- ✅ Uses **tiktoken** for accurate counting (optional)

### Benefits
- ✅ **Better performance insight**: Know actual LLM work done
- ✅ **Accurate cost tracking**: Predict API costs precisely
- ✅ **Fair comparisons**: Normalize for answer length
- ✅ **Production ready**: Metrics align with LLM billing

### How to Use
1. Run benchmark: `python benchmark_cache_performance.py`
2. Check "Throughput (tokens/sec)" in results
3. Compare with/without cache token rates
4. Use for capacity planning and optimization

---

*Token throughput measurement added: November 27, 2025*


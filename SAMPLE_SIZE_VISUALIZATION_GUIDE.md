# Sample Size Trend Visualization Guide

## 🎯 Overview

This guide explains how to visualize how cache strategy metrics change across different sample sizes (number of test queries).

---

## 📊 What You Get

**5 comprehensive trend visualizations** showing how metrics evolve as sample size increases:

1. **Token Throughput Trends** - How aggregate and per-query throughput change
2. **Cache Performance Trends** - Hit rate, cache hits, and latency trends
3. **Speedup Trends** - How speedup factors change with sample size
4. **Normalizer Impact Trend** - How normalizer benefits change with scale
5. **Comprehensive Dashboard** - All metrics in one view

---

## 🚀 Quick Start

### Step 1: Run Multi-Sample-Size Benchmark

```bash
python benchmark_multiple_sample_sizes.py
```

**What it does:**
- Tests 3 strategies (No Cache, LRU Basic, LRU + Normalizer)
- Tests across multiple sample sizes (default: 10, 20, 30, 50, 100)
- Saves results to `cache_strategies_multiple_sizes.json`

**Time:** ~15-30 minutes (depends on sample sizes)

### Step 2: Generate Trend Visualizations

```bash
python visualize_sample_size_trends.py
```

**What it does:**
- Reads `cache_strategies_multiple_sizes.json`
- Creates 5 PNG files with trend charts
- Opens charts automatically

**Time:** ~5 seconds

---

## 📈 Generated Visualizations

### 1. Token Throughput Trends
**File:** `sample_size_token_throughput_trends.png`

**Shows:**
- **Left Panel**: Aggregate throughput trend (total tokens / total time)
- **Right Panel**: Per-query throughput trend (avg tokens/sec per query)

**What to look for:**
- Does throughput stabilize or improve with more queries?
- Which strategy maintains best performance at scale?
- How does caching affect throughput as sample size grows?

**Example insights:**
```
Small samples (10-20): Cache has less impact
Large samples (50-100): Cache shows clear benefits
Normalizer: Consistent improvement across all sizes
```

---

### 2. Cache Performance Trends
**File:** `sample_size_cache_performance_trends.png`

**Shows (3 panels):**
- **Left**: Hit rate trend (%)
- **Middle**: Cache hits trend (count)
- **Right**: Average latency trend (seconds)

**What to look for:**
- Does hit rate improve with more queries? (More repetition = more hits)
- How many cache hits accumulate?
- Does latency decrease as cache fills?

**Example insights:**
```
Hit Rate: Increases with sample size (more repetition)
Cache Hits: Linear growth (more queries = more hits)
Latency: Decreases as cache effectiveness improves
```

---

### 3. Speedup Trends
**File:** `sample_size_speedup_trends.png`

**Shows (2 panels):**
- **Left**: Latency speedup vs no cache
- **Right**: Throughput speedup vs no cache

**What to look for:**
- Does speedup increase with sample size?
- Which strategy provides best speedup?
- At what sample size does caching become most effective?

**Example insights:**
```
Small samples: 1.5-2.0x speedup
Large samples: 2.0-2.5x speedup
Normalizer: +0.2-0.3x additional speedup
```

---

### 4. Normalizer Impact Trend
**File:** `sample_size_normalizer_impact_trend.png`

**Shows (2 panels):**
- **Left**: Hit rate gain from normalizer (%)
- **Right**: Throughput gain from normalizer (%)

**What to look for:**
- Does normalizer benefit increase with sample size?
- Is normalizer more effective at larger scales?
- What's the consistent improvement?

**Example insights:**
```
Hit Rate Gain: +10-15% across all sizes
Throughput Gain: +15-25% across all sizes
Consistent: Normalizer works at all scales
```

---

### 5. Comprehensive Dashboard
**File:** `sample_size_comprehensive_dashboard.png`

**Shows:**
- 9 subplots covering all key metrics
- Trends for all 3 strategies
- Speedup comparisons
- Normalizer impact

**Perfect for:**
- Presentations
- Reports
- Quick overview
- Documentation

---

## 🔧 Customization

### Change Sample Sizes

Edit `benchmark_multiple_sample_sizes.py`, line ~490:

```python
# Default
sample_sizes = [10, 20, 30, 50, 100]

# Custom
sample_sizes = [5, 15, 25, 40, 60, 80, 100, 150]
```

**Considerations:**
- More sizes = longer benchmark time
- Larger sizes = better cache effectiveness testing
- Smaller sizes = faster testing

### Adjust Colors/Styles

Edit `visualize_sample_size_trends.py`:

```python
# Line colors
colors = {
    'No Cache': '#e74c3c',           # Red
    'LRU Cache (Basic)': '#f39c12',   # Orange
    'LRU Cache + Normalizer': '#2ecc71'  # Green
}

# Markers
markers = {
    'No Cache': 'o',                  # Circle
    'LRU Cache (Basic)': 's',         # Square
    'LRU Cache + Normalizer': '^'     # Triangle
}
```

---

## 📊 Understanding the Trends

### Expected Patterns

#### 1. Hit Rate Increases
```
Why: More queries = more repetition = more cache hits

Small (10):  30-40% hit rate
Medium (30): 50-60% hit rate
Large (100): 60-70% hit rate
```

#### 2. Throughput Improves
```
Why: More cache hits = faster queries = higher throughput

Small (10):  20-25 tokens/sec
Medium (30): 30-35 tokens/sec
Large (100): 35-40 tokens/sec
```

#### 3. Latency Decreases
```
Why: Cache hits are much faster than misses

Small (10):  6-8 seconds (mostly misses)
Medium (30): 4-5 seconds (mixed)
Large (100): 3-4 seconds (many hits)
```

#### 4. Speedup Increases
```
Why: More cache hits = bigger performance gap vs no cache

Small (10):  1.5-1.8x speedup
Medium (30): 1.8-2.0x speedup
Large (100): 2.0-2.3x speedup
```

---

## 💡 Key Insights to Look For

### ✅ Good Results

1. **Hit Rate Increases with Sample Size**
   - Shows cache is working
   - More queries = more repetition = more hits

2. **Throughput Improves with Sample Size**
   - Cache becomes more effective
   - System handles more load

3. **Normalizer Provides Consistent Benefit**
   - Works at all scales
   - +10-20% hit rate improvement

4. **Speedup Increases with Scale**
   - Caching more valuable at larger scales
   - Better ROI with more queries

### ⚠️ Red Flags

1. **Hit Rate Doesn't Increase**
   - Questions may be too diverse
   - Cache may not be effective
   - Check cache key generation

2. **Throughput Decreases**
   - May indicate cache overhead
   - Check for memory issues
   - Review cache implementation

3. **Normalizer Has No Impact**
   - Questions may not have variations
   - Normalizer may not be working
   - Check test data generation

---

## 📁 Output Files

### Benchmark Output
```
cache_strategies_multiple_sizes.json
```

**Structure:**
```json
{
  "timestamp": "2025-11-27 10:30:00",
  "sample_sizes": [10, 20, 30, 50, 100],
  "results": [
    {
      "sample_size": 10,
      "strategies": {
        "No Cache": { ... },
        "LRU Cache (Basic)": { ... },
        "LRU Cache + Normalizer": { ... }
      }
    },
    ...
  ]
}
```

### Visualization Outputs
```
sample_size_token_throughput_trends.png      (2 panels)
sample_size_cache_performance_trends.png     (3 panels)
sample_size_speedup_trends.png               (2 panels)
sample_size_normalizer_impact_trend.png      (2 panels)
sample_size_comprehensive_dashboard.png      (9 panels)
```

---

## 🎨 Chart Examples

### Token Throughput Trend
```
Aggregate Throughput
┌─────────────────────────────────────┐
│                                     │
│  No Cache ────────────────          │
│  LRU Basic ────────────────        │
│  LRU+Norm ────────────────         │
│                                     │
│  10   20   30   50   100            │
│         Sample Size                 │
└─────────────────────────────────────┘

Trend: Throughput increases with sample size
       (More cache hits = faster queries)
```

### Hit Rate Trend
```
Cache Hit Rate
┌─────────────────────────────────────┐
│                                     │
│  No Cache ──────────────── (0%)    │
│  LRU Basic ──────────────── (50%)   │
│  LRU+Norm ──────────────── (65%)    │
│                                     │
│  10   20   30   50   100            │
│         Sample Size                 │
└─────────────────────────────────────┘

Trend: Hit rate increases with sample size
       (More repetition = more hits)
```

---

## 🔍 Troubleshooting

### "No results found"

**Solution:**
```bash
# Run benchmark first
python benchmark_multiple_sample_sizes.py

# Then visualize
python visualize_sample_size_trends.py
```

### Benchmark takes too long

**Solution:**
```python
# Reduce sample sizes in benchmark_multiple_sample_sizes.py
sample_sizes = [10, 20, 30]  # Instead of [10, 20, 30, 50, 100]
```

### Charts don't show trends

**Check:**
- Are sample sizes different enough?
- Did benchmark complete successfully?
- Are there enough data points?

### Memory issues

**Solution:**
```python
# Reduce sample sizes
sample_sizes = [10, 20, 30]  # Smaller sizes

# Or reduce cache size
LRUDataManager(cache_size=64)  # Instead of 128
```

---

## 📈 Interpreting Results

### Example Analysis

**Scenario:** Testing 10, 20, 30, 50, 100 queries

**Results:**
```
Sample Size | Hit Rate | Throughput | Speedup
────────────┼──────────┼────────────┼─────────
10          | 35%      | 25 t/s     | 1.5x
20          | 45%      | 30 t/s     | 1.7x
30          | 55%      | 35 t/s     | 1.9x
50          | 60%      | 38 t/s     | 2.1x
100         | 65%      | 40 t/s     | 2.2x
```

**Insights:**
- ✅ Hit rate increases with sample size (more repetition)
- ✅ Throughput improves (more cache hits)
- ✅ Speedup increases (caching more valuable at scale)
- ✅ Normalizer adds +10-15% hit rate consistently

---

## 🎯 Use Cases

### 1. **Capacity Planning**
```
Question: "How does system perform at different scales?"

Answer: Look at throughput trends
- Small scale: 20-25 tokens/sec
- Medium scale: 30-35 tokens/sec
- Large scale: 35-40 tokens/sec
```

### 2. **Cache Sizing**
```
Question: "What cache size do I need?"

Answer: Look at hit rate trends
- If hit rate plateaus early → cache too small
- If hit rate keeps increasing → cache effective
```

### 3. **Optimization ROI**
```
Question: "Is normalizer worth it?"

Answer: Look at normalizer impact trend
- Consistent +10-20% improvement
- Works at all scales
- Zero overhead
```

### 4. **Performance Scaling**
```
Question: "Does caching scale well?"

Answer: Look at speedup trends
- Speedup increases with scale
- More queries = better cache ROI
- System scales efficiently
```

---

## ✅ Summary

### What You Get

1. ✅ **Multi-sample-size benchmark** (tests 3 strategies across sizes)
2. ✅ **5 trend visualizations** (line plots showing changes)
3. ✅ **Comprehensive dashboard** (all metrics in one view)
4. ✅ **Normalizer impact analysis** (how benefits change with scale)
5. ✅ **Publication-quality charts** (300 DPI)

### Key Metrics Tracked

- Token throughput (aggregate + per-query)
- Cache hit rate
- Cache hits/misses
- Average latency
- Speedup factors
- Normalizer impact

### How to Use

```bash
# 1. Run benchmark (15-30 min)
python benchmark_multiple_sample_sizes.py

# 2. Visualize trends (5 sec)
python visualize_sample_size_trends.py

# 3. Review charts
# Files automatically saved and opened
```

---

## 🎓 Best Practices

### 1. Start Small
```python
# First test with small sizes
sample_sizes = [10, 20, 30]

# Then expand if needed
sample_sizes = [10, 20, 30, 50, 100]
```

### 2. Use Consistent Test Data
```python
# Same base questions for all sizes
# Ensures fair comparison
```

### 3. Review Trends, Not Just Points
```
Don't just look at individual values
Look at the overall trend:
- Increasing? Good!
- Decreasing? Investigate
- Flat? May indicate issue
```

### 4. Compare Strategies
```
Always compare all 3 strategies:
- No Cache (baseline)
- LRU Basic (caching)
- LRU + Normalizer (optimized)
```

---

*Sample size trend visualization guide - November 27, 2025*


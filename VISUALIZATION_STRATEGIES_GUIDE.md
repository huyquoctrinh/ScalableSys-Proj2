# Cache Strategy Visualization Guide

## 🎨 Overview

The `visualize_cache_strategies.py` script creates **6 comprehensive visualizations** comparing the three caching strategies with token throughput analysis.

---

## 📊 Visualizations Created

### 1. **Token Throughput Comparison** ⭐
**File:** `strategy_token_throughput.png`

**Shows:**
- **Left Panel**: Aggregate token throughput (total tokens / total time)
- **Right Panel**: Per-query token throughput (average tokens/sec per query)

**Why Both?**
- **Aggregate**: System-wide capacity (e.g., "Can handle 100 tokens/sec")
- **Per-Query**: User experience (e.g., "Each query gets ~50 tokens/sec on average")

**Example:**
```
Aggregate Throughput:
  No Cache:            18.5 tokens/sec
  LRU Basic:           32.5 tokens/sec
  LRU + Normalizer:    38.7 tokens/sec

Per-Query Throughput:
  No Cache:            22.3 tokens/sec
  LRU Basic:           45.2 tokens/sec
  LRU + Normalizer:    52.1 tokens/sec
```

---

### 2. **Cache Performance Metrics** ⭐
**File:** `strategy_cache_performance.png`

**Shows (3 panels):**
- **Left**: Cache hit rate (%)
- **Middle**: Cache hits vs misses (stacked bar)
- **Right**: Average query latency

**Example:**
```
Hit Rates:
  No Cache:            0.0%
  LRU Basic:           53.3%
  LRU + Normalizer:    66.7%  ← +13.4% boost!
```

---

### 3. **Speedup Factors** ⭐
**File:** `strategy_speedup_factors.png`

**Shows:**
- Latency speedup vs no cache
- Throughput speedup vs no cache
- Side-by-side comparison

**Example:**
```
Speedup (vs No Cache):
  LRU Basic:           1.76x throughput, 1.87x latency
  LRU + Normalizer:    2.09x throughput, 2.31x latency  ← Best!
```

---

### 4. **Improvement Breakdown** ⭐
**File:** `strategy_improvements.png`

**Shows (2 panels):**
- **Left**: Token throughput improvement (%)
- **Right**: Latency improvement (%)

**Example:**
```
Improvements vs No Cache:
  LRU Basic:           +75.7% throughput, +46.5% latency
  LRU + Normalizer:    +109.2% throughput, +56.8% latency
```

---

### 5. **Normalizer Impact Analysis** ⭐⭐
**File:** `normalizer_impact.png`

**Shows:**
- **Left**: Hit rate comparison (LRU basic vs LRU + Normalizer)
- **Right**: Throughput comparison
- **Green arrows**: Show improvement from normalizer

**Example:**
```
Query Normalizer Impact:
  Hit Rate:      +13.4%
  Throughput:    +19.1%
```

This chart specifically highlights what the **Query Normalizer adds**!

---

### 6. **Summary Dashboard** ⭐⭐⭐
**File:** `strategy_dashboard.png`

**Comprehensive view with:**
- Aggregate throughput
- Per-query throughput
- Cache hit rates
- Average latency
- Speedup factors
- Total tokens
- **Summary table** with all key metrics

**Perfect for presentations and reports!**

---

## 🚀 How to Use

### Step 1: Run Benchmark

```bash
python benchmark_cache_strategies.py
```

This generates `cache_strategies_results.json`

### Step 2: Generate Visualizations

```bash
python visualize_cache_strategies.py
```

### Step 3: View Results

Opens automatically, and saves 6 PNG files:
1. `strategy_token_throughput.png`
2. `strategy_cache_performance.png`
3. `strategy_speedup_factors.png`
4. `strategy_improvements.png`
5. `normalizer_impact.png`
6. `strategy_dashboard.png`

---

## 📈 Understanding the Charts

### Token Throughput Charts

#### Aggregate Throughput
```
Shows: System-wide tokens/sec
Formula: Total tokens / Total time

Example:
  3,450 tokens in 186s = 18.5 tokens/sec

Use for:
  - Capacity planning ("Can handle X tokens/sec")
  - Cost estimation (tokens → API costs)
  - System scaling decisions
```

#### Per-Query Throughput
```
Shows: Average tokens/sec for individual queries
Formula: Mean of (tokens per query / latency per query)

Example:
  Query 1: 120 tokens / 6.2s = 19.4 tokens/sec
  Query 2: 100 tokens / 0.8s = 125.0 tokens/sec (cache hit!)
  Average: 72.2 tokens/sec

Use for:
  - User experience ("Typical query gets X tokens/sec")
  - SLA planning
  - Understanding query variability
```

#### Why They Differ
```
Cache hits are MUCH faster:
  Cache miss: ~15-20 tokens/sec
  Cache hit: ~100-150 tokens/sec

Per-query average includes both:
  (20 + 20 + 125 + 150) / 4 = 78.75 tokens/sec

Aggregate accounts for total time:
  (120 + 100 + 100 + 110) / 30s = 17.67 tokens/sec
  
Both are correct, just measure different things!
```

---

### Cache Performance Charts

#### Hit Rate
```
Higher = Better

Good: 60-80% hit rate
Excellent: 80%+ hit rate

Query Normalizer typically adds: +10-20% hit rate
```

#### Hits vs Misses (Stacked Bar)
```
Visual breakdown of cache effectiveness

Green = Cache hits (fast queries)
Red = Cache misses (slow queries)

More green = better performance
```

---

### Speedup Charts

#### Speedup Factors
```
Shows: How many times faster than baseline

2.0x = Twice as fast
3.0x = Three times as fast

Formula: Baseline latency / Strategy latency
```

#### Improvement Percentages
```
Shows: Percentage improvement

+50% = Half the latency
+100% = Twice as fast

Formula: (Baseline - Strategy) / Baseline × 100
```

---

## 💡 What to Look For

### Good Results

✅ **LRU + Normalizer should show:**
- Highest hit rate (60-70%)
- Highest throughput (35-45 tokens/sec aggregate)
- Highest speedup (2.0-2.5x)
- 10-20% better than basic LRU

✅ **Clear progression:**
- No Cache < LRU Basic < LRU + Normalizer
- Each strategy better than previous

### Red Flags

⚠️ **Normalizer not helping:**
- Similar hit rate to basic LRU
- Check if test questions have variations
- May need more diverse test set

⚠️ **Low overall hit rates (<40%):**
- Questions may be too diverse
- Consider larger cache size
- Check cache key generation

⚠️ **Small speedups (<1.5x):**
- Cache may not be effective
- Review caching strategy
- Check for expensive answer generation

---

## 🎯 Customization

### Change Colors

```python
# In each plotting function
colors = ['#e74c3c', '#f39c12', '#2ecc71']  # Red, Orange, Green

# Custom colors
colors = ['#95a5a6', '#3498db', '#9b59b6']  # Gray, Blue, Purple
```

### Adjust Figure Sizes

```python
# Make figures larger
fig, axes = plt.subplots(1, 2, figsize=(18, 8))  # Was (14, 6)

# Make dashboard bigger
fig = plt.figure(figsize=(20, 14))  # Was (16, 12)
```

### Add More Metrics

```python
# In plot_token_throughput_comparison:
# Add median throughput
median_throughput = [s['median_tokens_per_sec_per_query'] for s in stats]
ax.plot(x, median_throughput, 'o-', label='Median', linewidth=2)
```

---

## 📁 Output Files

### Generated Images

1. **strategy_token_throughput.png**
   - Dual panel: aggregate vs per-query
   - Shows both throughput metrics
   - Color-coded by strategy

2. **strategy_cache_performance.png**
   - Triple panel: hit rate, hits/misses, latency
   - Complete cache analysis
   - Stacked bars for hits/misses

3. **strategy_speedup_factors.png**
   - Side-by-side speedup comparison
   - Latency and throughput speedups
   - Baseline reference line

4. **strategy_improvements.png**
   - Improvement percentages
   - Easy comparison to baseline
   - Shows relative gains

5. **normalizer_impact.png** ⭐
   - Focuses on normalizer benefits
   - Green arrows show improvement
   - Clear before/after comparison

6. **strategy_dashboard.png** ⭐⭐
   - All metrics in one view
   - Summary table at bottom
   - Publication quality

---

## 🖼️ Chart Descriptions

### Strategy Token Throughput
```
┌─────────────────────────────────────────────────┐
│     Token Throughput Comparison                 │
├──────────────────────┬──────────────────────────┤
│ Aggregate Throughput │ Per-Query Throughput     │
│                      │                          │
│ [Bar chart]          │ [Bar chart]              │
│ No Cache: 18.5       │ No Cache: 22.3           │
│ LRU: 32.5            │ LRU: 45.2                │
│ LRU+Norm: 38.7       │ LRU+Norm: 52.1           │
└──────────────────────┴──────────────────────────┘
```

### Cache Performance
```
┌──────────────────────────────────────────────────────┐
│           Cache Performance Metrics                  │
├──────────────┬──────────────┬─────────────────────┤
│ Hit Rate (%) │ Hits/Misses  │ Avg Latency (s)     │
│              │              │                     │
│ [Bar chart]  │ [Stacked]    │ [Bar chart]         │
│ 0%, 53%, 67% │ Green/Red    │ 8.0, 4.3, 3.5       │
└──────────────┴──────────────┴─────────────────────┘
```

### Normalizer Impact
```
┌─────────────────────────────────────────────┐
│     Query Normalizer Impact Analysis        │
├────────────────────┬────────────────────────┤
│ Hit Rate           │ Throughput             │
│                    │                        │
│ LRU: 53.3%    ─┐   │ LRU: 32.5 t/s     ─┐   │
│               ─┘   │                   ─┘   │
│ +Norm: 66.7%       │ +Norm: 38.7 t/s        │
│                    │                        │
│ Gain: +13.4%       │ Gain: +19.1%           │
└────────────────────┴────────────────────────┘
```

---

## 🔍 Troubleshooting

### "No results found"

**Solution:**
```bash
# Run benchmark first
python benchmark_cache_strategies.py

# Then visualize
python visualize_cache_strategies.py
```

### "Module not found: matplotlib"

**Solution:**
```bash
pip install matplotlib
# or
uv add matplotlib
```

### Charts don't open automatically

**Solution:**
The PNG files are saved anyway. Open manually:
```bash
# Windows
start strategy_dashboard.png

# Linux
xdg-open strategy_dashboard.png

# Mac
open strategy_dashboard.png
```

---

## 📊 Example Analysis

### Using the Charts

#### Find the Best Strategy
```
Look at strategy_speedup_factors.png:
- LRU + Normalizer has highest bars
- 2.09x throughput speedup
- Clearly the winner!
```

#### Quantify Normalizer Benefit
```
Look at normalizer_impact.png:
- Green arrows show improvement
- +13.4% hit rate
- +19.1% throughput
- Proves normalizer is worth it!
```

#### Present to Stakeholders
```
Use strategy_dashboard.png:
- All metrics in one view
- Professional layout
- Easy to understand
- Summary table at bottom
```

---

## 🎓 Best Practices

### 1. Run Benchmark First

```bash
# Always generate fresh data
python benchmark_cache_strategies.py
```

### 2. Check Data Quality

```python
import json
with open('cache_strategies_results.json', 'r') as f:
    data = json.load(f)

# Verify all strategies present
print(f"Strategies: {len(data['strategies'])}")
# Should be 3
```

### 3. Customize for Your Needs

```python
# Edit visualize_cache_strategies.py
# Change colors, sizes, labels as needed
```

### 4. Save for Documentation

```bash
# Charts are publication-quality (300 DPI)
# Perfect for reports, presentations, documentation
```

---

## 📈 Interpreting Results

### Good Benchmark Results

```
✅ Normalizer Impact:
   Hit rate: +10-20%
   Throughput: +15-30%

✅ LRU vs No Cache:
   Hit rate: 50-60%
   Speedup: 1.8-2.0x

✅ Overall:
   Best strategy 2x+ faster than baseline
```

### Investigate If:

```
⚠️ Normalizer adds <5% hit rate:
   - Test questions may lack variations
   - Check normalizer is working
   - Review test data generation

⚠️ LRU hit rate <40%:
   - Cache may be too small
   - Questions too diverse
   - Need semantic caching

⚠️ All strategies similar:
   - Cache not working properly
   - Check implementation
   - Review cache key generation
```

---

## 🚀 Quick Start

### Complete Workflow

```bash
# 1. Run benchmark (3-5 minutes)
python benchmark_cache_strategies.py

# 2. Generate visualizations (5 seconds)
python visualize_cache_strategies.py

# 3. Review charts
# Files automatically saved to current directory
```

### Output Files

```
strategy_token_throughput.png    ← Token metrics (2 panels)
strategy_cache_performance.png   ← Cache metrics (3 panels)
strategy_speedup_factors.png     ← Speedup comparison
strategy_improvements.png        ← Improvement percentages
normalizer_impact.png            ← Normalizer benefits ⭐
strategy_dashboard.png           ← Complete dashboard ⭐⭐
```

---

## 💡 Use Cases

### 1. **Prove Normalizer Value**

Show `normalizer_impact.png` to demonstrate:
- Concrete hit rate improvement
- Measurable throughput gains
- Zero overhead (just normalization)

### 2. **Choose Cache Strategy**

Compare all three in `strategy_dashboard.png`:
- See full metrics at once
- Make data-driven decision
- Document your choice

### 3. **Present Performance**

Use `strategy_speedup_factors.png` for:
- Stakeholder presentations
- Performance reports
- Optimization justification

### 4. **Optimize Further**

Analyze `strategy_cache_performance.png`:
- If hit rate low → increase cache size
- If latency high → check query generation
- If misses high → consider semantic caching

---

## 🎨 Customization Examples

### Change Chart Style

```python
# In any plotting function
plt.style.use('seaborn-v0_8-darkgrid')  # Different style

# Or customize individually
ax.set_facecolor('#f0f0f0')  # Light gray background
ax.grid(True, linestyle='--', alpha=0.5)  # Dashed gridlines
```

### Add Annotations

```python
# In plot_normalizer_impact:
ax.text(0.5, 0.9, 'Normalizer adds +13.4% hit rate!',
        transform=ax.transAxes,
        ha='center',
        fontsize=14,
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
```

### Modify Colors

```python
# Colorblind-friendly palette
colors = ['#d62728', '#ff7f0e', '#2ca02c']  # Red, Orange, Green

# High-contrast
colors = ['#000000', '#666666', '#00ff00']  # Black, Gray, Bright Green

# Corporate branding
colors = ['#yourcolor1', '#yourcolor2', '#yourcolor3']
```

---

## 📊 Sample Dashboard Layout

```
┌───────────────────────────────────────────────────────┐
│        Cache Strategy Performance Dashboard          │
├──────────────┬──────────────┬────────────────────────┤
│ Aggregate    │ Per-Query    │ Hit Rate               │
│ Throughput   │ Throughput   │                        │
│ 18.5, 32.5,  │ 22.3, 45.2,  │ 0%, 53%,               │
│ 38.7 t/s     │ 52.1 t/s     │ 67%                    │
├──────────────┼──────────────┼────────────────────────┤
│ Avg Latency  │ Speedup      │ Total Tokens           │
│ 8.0, 4.3,    │ 1.0x, 1.8x,  │ 3,450,                 │
│ 3.5s         │ 2.1x         │ 3,465, 3,458           │
├──────────────┴──────────────┴────────────────────────┤
│                  Summary Table                        │
│ Strategy        Hit%  Agg    Per-Q  Speedup  Improve │
│ No Cache        0.0   18.5   22.3   1.00x    base    │
│ LRU Basic       53.3  32.5   45.2   1.76x    +75.7%  │
│ LRU+Normalizer  66.7  38.7   52.1   2.09x    +109.2% │
└───────────────────────────────────────────────────────┘
```

---

## ✅ Summary

### What You Get

1. ✅ **6 publication-quality charts**
2. ✅ **Token throughput analysis** (aggregate + per-query)
3. ✅ **3-way strategy comparison**
4. ✅ **Normalizer impact visualization**
5. ✅ **Comprehensive dashboard**
6. ✅ **300 DPI images** (print-ready)

### Key Charts

- **For analysis**: Token throughput, Cache performance
- **For decisions**: Speedup factors, Improvements
- **For presentations**: Normalizer impact, Dashboard
- **For documentation**: All of them!

### How to Use

```bash
# 1. Run benchmark
python benchmark_cache_strategies.py

# 2. Visualize
python visualize_cache_strategies.py

# 3. Use charts in reports/presentations
```

---

## 🎯 Next Steps

1. ✅ Review this guide
2. ⬜ Run benchmark
3. ⬜ Generate visualizations
4. ⬜ Analyze results
5. ⬜ Share findings

---

*Visualization guide for cache strategies - November 27, 2025*


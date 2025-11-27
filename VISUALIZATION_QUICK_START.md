# Visualization Quick Start

## 🚀 Generate Visualizations in 2 Steps

### Step 1: Run Benchmark
```bash
python benchmark_cache_strategies.py
```
⏱️ Takes ~3-5 minutes, generates `cache_strategies_results.json`

### Step 2: Create Charts
```bash
python visualize_cache_strategies.py
```
⏱️ Takes ~5 seconds, generates **6 PNG files**

---

## 📊 6 Visualizations Created

| File | What It Shows | Use For |
|------|---------------|---------|
| `strategy_token_throughput.png` | Aggregate + Per-query throughput | Understanding both throughput types |
| `strategy_cache_performance.png` | Hit rate, hits/misses, latency | Analyzing cache effectiveness |
| `strategy_speedup_factors.png` | Latency & throughput speedups | Quantifying performance gains |
| `strategy_improvements.png` | % improvement vs baseline | Showing relative benefits |
| `normalizer_impact.png` ⭐ | Normalizer-specific gains | Proving normalizer value |
| `strategy_dashboard.png` ⭐⭐ | Complete overview + table | Presentations & reports |

---

## 🎯 Key Metrics Explained

### Token Throughput (2 Types)

#### 1. Aggregate Throughput
```
Formula: Total tokens / Total time
Example: 3,450 tokens / 186s = 18.5 tokens/sec

What it means: System-wide capacity
Use for: "My system can handle X tokens/sec"
```

#### 2. Per-Query Throughput
```
Formula: Average of (query tokens / query latency)
Example: Mean(120/6.2, 100/0.8, ...) = 52.1 tokens/sec

What it means: Typical user experience
Use for: "Users get X tokens/sec on average"
```

#### Why They Differ
```
Cache hits are MUCH faster:
  Miss: ~15-20 tokens/sec
  Hit: ~100-150 tokens/sec

Per-query includes fast hits → Higher average
Aggregate accounts for total time → Lower overall
```

---

## 📈 Expected Results

### Good Benchmark
```
Strategy              Hit Rate   Agg t/s   Per-Q t/s   Speedup
─────────────────────────────────────────────────────────────
No Cache              0.0%       18.5      22.3        1.00x
LRU Cache             53.3%      32.5      45.2        1.76x
LRU + Normalizer      66.7%      38.7      52.1        2.09x
```

### Normalizer Impact
```
✅ +10-20% hit rate improvement
✅ +15-30% throughput increase
✅ Clear green bars showing gains
```

---

## 🔍 Which Chart to Use When

### For Analysis
- **Token Throughput**: Compare system capacity vs user experience
- **Cache Performance**: Understand hit rates and latency

### For Decisions
- **Speedup Factors**: Quantify improvements
- **Improvements**: See percentage gains

### For Presentations
- **Normalizer Impact**: Show specific normalizer value
- **Dashboard**: Complete overview in one chart

### For Documentation
- **All 6 charts**: Complete performance analysis

---

## 💡 Quick Tips

### 1. Run Fresh Data
```bash
# Always generate new benchmark before visualizing
python benchmark_cache_strategies.py
python visualize_cache_strategies.py
```

### 2. Check 3 Strategies
The benchmark should test:
1. ❌ No Cache (baseline)
2. ✅ LRU Cache (basic caching)
3. ✅ LRU + Normalizer (optimized)

### 3. Focus on Key Metrics
- **Hit Rate**: Should increase with normalizer
- **Throughput**: Should be 2x+ with caching
- **Speedup**: Compare all strategies

### 4. Use Dashboard for Presentations
The `strategy_dashboard.png` includes:
- All 6 key metrics as charts
- Summary table at bottom
- Professional layout
- 300 DPI quality

---

## 🎨 What Each Chart Looks Like

### Token Throughput (2 panels)
```
┌────────────────────┬────────────────────┐
│ Aggregate          │ Per-Query          │
│ [Bar: 18.5]        │ [Bar: 22.3]        │
│ [Bar: 32.5]        │ [Bar: 45.2]        │
│ [Bar: 38.7]        │ [Bar: 52.1]        │
└────────────────────┴────────────────────┘
```

### Cache Performance (3 panels)
```
┌──────────┬──────────┬──────────┐
│ Hit Rate │ Hits vs  │ Latency  │
│ (%)      │ Misses   │ (sec)    │
│ [Bars]   │ [Stack]  │ [Bars]   │
└──────────┴──────────┴──────────┘
```

### Normalizer Impact (2 panels) ⭐
```
┌────────────────┬────────────────┐
│ Hit Rate       │ Throughput     │
│ Before: 53.3%  │ Before: 32.5   │
│   ↓ +13.4%     │   ↓ +19.1%     │
│ After: 66.7%   │ After: 38.7    │
└────────────────┴────────────────┘
```

### Dashboard (6 metrics + table) ⭐⭐
```
┌─────────┬─────────┬─────────┐
│ Agg T   │ Per-Q T │ Hit %   │
├─────────┼─────────┼─────────┤
│ Latency │ Speedup │ Tokens  │
├─────────┴─────────┴─────────┤
│      Summary Table          │
│  [All metrics in table]     │
└─────────────────────────────┘
```

---

## 🐛 Troubleshooting

### "No results found"
```bash
# Run benchmark first
python benchmark_cache_strategies.py
```

### Charts don't open
```bash
# Files are saved anyway
# Open manually in current directory
```

### Missing matplotlib
```bash
pip install matplotlib
# or
uv add matplotlib
```

---

## ✅ Checklist

- [ ] Run benchmark: `python benchmark_cache_strategies.py`
- [ ] Generate charts: `python visualize_cache_strategies.py`
- [ ] Check 6 PNG files created
- [ ] Review dashboard for overview
- [ ] Check normalizer impact chart
- [ ] Use charts in documentation/presentation

---

## 📁 Output Files Summary

```
After running visualize_cache_strategies.py:

strategy_token_throughput.png    2-panel throughput comparison
strategy_cache_performance.png   3-panel cache analysis
strategy_speedup_factors.png     Speedup bars with baseline
strategy_improvements.png        Percentage improvements
normalizer_impact.png            Normalizer-specific gains ⭐
strategy_dashboard.png           Complete dashboard ⭐⭐
```

---

## 🎯 One-Line Summary

**Run benchmark → Generate 6 charts → Use dashboard for presentations**

---

*Quick start for visualization - November 27, 2025*


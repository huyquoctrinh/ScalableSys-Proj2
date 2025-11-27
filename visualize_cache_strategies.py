"""
Visualization script for cache strategy benchmark results.
Creates charts comparing No Cache, LRU Cache, and LRU Cache + Normalizer.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List


def load_results(filename: str = "cache_strategies_results.json") -> Dict:
    """Load benchmark results from JSON file."""
    if not Path(filename).exists():
        print(f"Error: {filename} not found.")
        print("Please run benchmark_cache_strategies.py first to generate results.")
        return None
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return data


def extract_stats(data: Dict) -> List[Dict]:
    """Extract statistics from benchmark data."""
    return [strategy['stats'] for strategy in data['strategies']]


def plot_token_throughput_comparison(stats: List[Dict]):
    """Plot token throughput comparison (aggregate vs per-query)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Token Throughput Comparison', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    x = np.arange(len(strategies))
    width = 0.6
    
    # Colors for the three strategies
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # Plot 1: Aggregate Token Throughput
    ax = axes[0]
    aggregate_throughput = [s['throughput_tokens_per_sec_aggregate'] for s in stats]
    
    bars = ax.bar(x, aggregate_throughput, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Tokens per Second', fontsize=12)
    ax.set_title('Aggregate Token Throughput\n(Total Tokens / Total Time)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Plot 2: Per-Query Token Throughput
    ax = axes[1]
    per_query_throughput = [s['avg_tokens_per_sec_per_query'] for s in stats]
    
    bars = ax.bar(x, per_query_throughput, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Tokens per Second', fontsize=12)
    ax.set_title('Per-Query Token Throughput\n(Average tokens/sec per query)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    return fig


def plot_cache_performance(stats: List[Dict]):
    """Plot cache performance metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Cache Performance Metrics', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    x = np.arange(len(strategies))
    width = 0.6
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # Plot 1: Cache Hit Rate
    ax = axes[0]
    hit_rates = [s['cache_hit_rate'] for s in stats]
    
    bars = ax.bar(x, hit_rates, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Hit Rate (%)', fontsize=12)
    ax.set_title('Cache Hit Rate', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.set_ylim([0, 100])
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Plot 2: Total Queries
    ax = axes[1]
    hits = [s['cache_hits'] for s in stats]
    misses = [s['cache_misses'] for s in stats]
    
    bars1 = ax.bar(x, hits, width, label='Cache Hits', color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x, misses, width, bottom=hits, label='Cache Misses', color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Number of Queries', fontsize=12)
    ax.set_title('Cache Hits vs Misses', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Plot 3: Average Latency
    ax = axes[2]
    avg_latency = [s['avg_latency'] for s in stats]
    
    bars = ax.bar(x, avg_latency, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Latency (seconds)', fontsize=12)
    ax.set_title('Average Query Latency', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    return fig


def plot_speedup_factors(stats: List[Dict]):
    """Plot speedup factors compared to no cache."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('Performance Speedup vs No Cache', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    baseline = stats[0]  # No Cache
    
    # Calculate speedups
    latency_speedups = [baseline['avg_latency'] / s['avg_latency'] for s in stats]
    throughput_speedups = [s['throughput_tokens_per_sec_aggregate'] / 
                           baseline['throughput_tokens_per_sec_aggregate'] for s in stats]
    
    x = np.arange(len(strategies))
    width = 0.35
    
    # Plot bars
    bars1 = ax.bar(x - width/2, latency_speedups, width, label='Latency Speedup',
                   color='#3498db', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, throughput_speedups, width, label='Throughput Speedup',
                   color='#9b59b6', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Speedup Factor (x)', fontsize=12)
    ax.set_title('Higher is Better', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Baseline (1.0x)')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}x',
                    ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    return fig


def plot_improvement_breakdown(stats: List[Dict]):
    """Plot improvement breakdown showing cache contributions."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Cache Strategy Improvement Analysis', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    baseline = stats[0]  # No Cache
    
    # Calculate improvements
    throughput_improvements = [
        (s['throughput_tokens_per_sec_aggregate'] - baseline['throughput_tokens_per_sec_aggregate']) / 
        baseline['throughput_tokens_per_sec_aggregate'] * 100
        for s in stats
    ]
    
    latency_improvements = [
        (baseline['avg_latency'] - s['avg_latency']) / baseline['avg_latency'] * 100
        for s in stats
    ]
    
    x = np.arange(len(strategies))
    width = 0.6
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # Plot 1: Throughput Improvement
    ax = axes[0]
    bars = ax.bar(x, throughput_improvements, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Improvement (%)', fontsize=12)
    ax.set_title('Token Throughput Improvement\nvs No Cache', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontweight='bold', fontsize=11)
    
    # Plot 2: Latency Improvement
    ax = axes[1]
    bars = ax.bar(x, latency_improvements, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Improvement (%)', fontsize=12)
    ax.set_title('Latency Improvement\nvs No Cache', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    return fig


def plot_latency_comparison(stats: List[Dict]):
    """Plot comprehensive latency comparison with detailed metrics."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Latency Comparison & Analysis', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    x = np.arange(len(strategies))
    width = 0.6
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # Plot 1: Latency Statistics (Min, Avg, Median, Max)
    ax = axes[0]
    
    # Prepare data for grouped bars
    min_latencies = [s['min_latency'] for s in stats]
    avg_latencies = [s['avg_latency'] for s in stats]
    median_latencies = [s['median_latency'] for s in stats]
    max_latencies = [s['max_latency'] for s in stats]
    
    x_pos = np.arange(len(strategies))
    bar_width = 0.2
    
    bars1 = ax.bar(x_pos - 1.5*bar_width, min_latencies, bar_width, 
                   label='Min', color='#2ecc71', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x_pos - 0.5*bar_width, avg_latencies, bar_width, 
                   label='Average', color='#3498db', alpha=0.8, edgecolor='black')
    bars3 = ax.bar(x_pos + 0.5*bar_width, median_latencies, bar_width, 
                   label='Median', color='#9b59b6', alpha=0.8, edgecolor='black')
    bars4 = ax.bar(x_pos + 1.5*bar_width, max_latencies, bar_width, 
                   label='Max', color='#e74c3c', alpha=0.8, edgecolor='black')
    
    ax.set_ylabel('Latency (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Statistics Comparison\n(Min, Average, Median, Max)', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels for average (most important)
    for i, (bar, val) in enumerate(zip(bars2, avg_latencies)):
        ax.text(bar.get_x() + bar.get_width()/2., val,
                f'{val:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Plot 2: Latency Distribution (Box plot style with error bars)
    ax = axes[1]
    
    # Create error bars showing min-max range
    yerr_lower = [avg - min_val for avg, min_val in zip(avg_latencies, min_latencies)]
    yerr_upper = [max_val - avg for avg, max_val in zip(avg_latencies, max_latencies)]
    
    bars = ax.bar(x, avg_latencies, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5,
                  yerr=[yerr_lower, yerr_upper], capsize=5, error_kw={'linewidth': 2, 'capthick': 2})
    
    # Add median markers
    for i, (x_pos, median) in enumerate(zip(x, median_latencies)):
        ax.plot([x_pos - width/2, x_pos + width/2], [median, median], 
               'k-', linewidth=2, alpha=0.7, label='Median' if i == 0 else '')
    
    ax.set_ylabel('Latency (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Distribution\n(Average with Min-Max Range)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bar, val in zip(bars, avg_latencies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Add legend for median line
    if len(median_latencies) > 0:
        ax.plot([], [], 'k-', linewidth=2, label='Median')
        ax.legend(fontsize=10, loc='upper left')
    
    plt.tight_layout()
    return fig


def plot_latency_breakdown(stats: List[Dict]):
    """Plot latency breakdown showing standard deviation and percentiles."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Latency Variability & Consistency Analysis', fontsize=16, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    x = np.arange(len(strategies))
    width = 0.6
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # Plot 1: Standard Deviation (variability)
    ax = axes[0]
    stdev_latencies = [s.get('stdev_latency', 0) for s in stats]
    
    bars = ax.bar(x, stdev_latencies, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Standard Deviation (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Variability\n(Lower = More Consistent)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bar, val in zip(bars, stdev_latencies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Plot 2: Latency Range (Max - Min)
    ax = axes[1]
    latency_ranges = [s['max_latency'] - s['min_latency'] for s in stats]
    
    bars = ax.bar(x, latency_ranges, width, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Latency Range (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Spread\n(Max - Min, Lower = More Predictable)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.split('. ')[1] if '. ' in s else s for s in strategies], rotation=15, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bar, val in zip(bars, latency_ranges):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    return fig


def plot_normalizer_impact(stats: List[Dict]):
    """Plot the specific impact of query normalizer."""
    if len(stats) < 3:
        print("Need at least 3 strategies to show normalizer impact")
        return None
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Query Normalizer Impact Analysis', fontsize=16, fontweight='bold')
    
    lru_basic = stats[1]  # LRU Cache (Basic)
    lru_normalized = stats[2]  # LRU Cache + Normalizer
    
    # Calculate normalizer contribution
    hit_rate_gain = lru_normalized['cache_hit_rate'] - lru_basic['cache_hit_rate']
    throughput_gain = ((lru_normalized['throughput_tokens_per_sec_aggregate'] - 
                       lru_basic['throughput_tokens_per_sec_aggregate']) / 
                      lru_basic['throughput_tokens_per_sec_aggregate'] * 100)
    
    # Plot 1: Hit Rate Comparison
    ax = axes[0]
    categories = ['LRU Basic', 'LRU +\nNormalizer']
    hit_rates = [lru_basic['cache_hit_rate'], lru_normalized['cache_hit_rate']]
    colors_cmp = ['#f39c12', '#2ecc71']
    
    bars = ax.bar(categories, hit_rates, color=colors_cmp, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Cache Hit Rate (%)', fontsize=12)
    ax.set_title(f'Normalizer adds +{hit_rate_gain:.1f}% hit rate', fontsize=12, fontweight='bold')
    ax.set_ylim([0, 100])
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Add arrow showing gain
    ax.annotate('', xy=(1, lru_normalized['cache_hit_rate']), xytext=(0, lru_basic['cache_hit_rate']),
                arrowprops=dict(arrowstyle='->', lw=2, color='green'))
    
    # Plot 2: Throughput Comparison
    ax = axes[1]
    throughputs = [lru_basic['throughput_tokens_per_sec_aggregate'],
                   lru_normalized['throughput_tokens_per_sec_aggregate']]
    
    bars = ax.bar(categories, throughputs, color=colors_cmp, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Token Throughput (tokens/sec)', fontsize=12)
    ax.set_title(f'Normalizer adds +{throughput_gain:.1f}% throughput', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Add arrow showing gain
    ax.annotate('', xy=(1, lru_normalized['throughput_tokens_per_sec_aggregate']), 
                xytext=(0, lru_basic['throughput_tokens_per_sec_aggregate']),
                arrowprops=dict(arrowstyle='->', lw=2, color='green'))
    
    plt.tight_layout()
    return fig


def create_summary_dashboard(stats: List[Dict]):
    """Create comprehensive summary dashboard."""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle('Cache Strategy Performance Dashboard', fontsize=18, fontweight='bold')
    
    strategies = [s['name'] for s in stats]
    baseline = stats[0]
    x = np.arange(len(strategies))
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    
    # 1. Aggregate Token Throughput
    ax1 = fig.add_subplot(gs[0, 0])
    throughputs = [s['throughput_tokens_per_sec_aggregate'] for s in stats]
    bars = ax1.bar(x, throughputs, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_title('Aggregate Throughput\n(tokens/sec)', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 2. Per-Query Token Throughput
    ax2 = fig.add_subplot(gs[0, 1])
    per_query = [s['avg_tokens_per_sec_per_query'] for s in stats]
    bars = ax2.bar(x, per_query, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_title('Per-Query Throughput\n(tokens/sec)', fontsize=11, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 3. Cache Hit Rate
    ax3 = fig.add_subplot(gs[0, 2])
    hit_rates = [s['cache_hit_rate'] for s in stats]
    bars = ax3.bar(x, hit_rates, color=colors, alpha=0.8, edgecolor='black')
    ax3.set_title('Cache Hit Rate\n(%)', fontsize=11, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax3.set_ylim([0, 100])
    ax3.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}%',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 4. Average Latency
    ax4 = fig.add_subplot(gs[1, 0])
    latencies = [s['avg_latency'] for s in stats]
    bars = ax4.bar(x, latencies, color=colors, alpha=0.8, edgecolor='black')
    ax4.set_title('Average Latency\n(seconds)', fontsize=11, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax4.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 5. Speedup Factors
    ax5 = fig.add_subplot(gs[1, 1])
    speedups = [s['throughput_tokens_per_sec_aggregate'] / baseline['throughput_tokens_per_sec_aggregate'] 
                for s in stats]
    bars = ax5.bar(x, speedups, color=colors, alpha=0.8, edgecolor='black')
    ax5.set_title('Throughput Speedup\n(vs No Cache)', fontsize=11, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax5.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
    ax5.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}x',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 6. Total Tokens Generated
    ax6 = fig.add_subplot(gs[1, 2])
    total_tokens = [s['total_tokens_generated'] for s in stats]
    bars = ax6.bar(x, total_tokens, color=colors, alpha=0.8, edgecolor='black')
    ax6.set_title('Total Tokens\nGenerated', fontsize=11, fontweight='bold')
    ax6.set_xticks(x)
    ax6.set_xticklabels([s.split('. ')[1][:10] if '. ' in s else s[:10] for s in strategies], fontsize=9)
    ax6.grid(axis='y', alpha=0.3)
    for bar in bars:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 7. Summary Table
    ax7 = fig.add_subplot(gs[2, :])
    ax7.axis('off')
    
    table_data = [
        ['Strategy', 'Hit Rate', 'Throughput\n(agg)', 'Throughput\n(per-query)', 'Speedup', 'Improvement']
    ]
    
    for i, s in enumerate(stats):
        speedup = s['throughput_tokens_per_sec_aggregate'] / baseline['throughput_tokens_per_sec_aggregate']
        improvement = ((s['throughput_tokens_per_sec_aggregate'] - 
                       baseline['throughput_tokens_per_sec_aggregate']) / 
                      baseline['throughput_tokens_per_sec_aggregate'] * 100)
        
        name = s['name'].split('. ')[1] if '. ' in s['name'] else s['name']
        table_data.append([
            name,
            f"{s['cache_hit_rate']:.1f}%",
            f"{s['throughput_tokens_per_sec_aggregate']:.1f} t/s",
            f"{s['avg_tokens_per_sec_per_query']:.1f} t/s",
            f"{speedup:.2f}x",
            f"+{improvement:.1f}%" if improvement > 0 else "baseline"
        ])
    
    table = ax7.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.25, 0.15, 0.15, 0.15, 0.15, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # Style header row
    for i in range(6):
        cell = table[(0, i)]
        cell.set_facecolor('#3498db')
        cell.set_text_props(weight='bold', color='white')
    
    # Color rows by strategy
    for i in range(1, len(table_data)):
        for j in range(6):
            table[(i, j)].set_facecolor(colors[i-1] if i <= len(colors) else 'white')
            table[(i, j)].set_alpha(0.3)
    
    return fig


def main():
    """Main visualization function."""
    print("="*80)
    print("CACHE STRATEGY BENCHMARK VISUALIZATION")
    print("="*80)
    
    # Load results
    data = load_results("cache_strategies_results.json")
    if not data:
        print("\nNo results found. Run benchmark first:")
        print("  python benchmark_cache_strategies.py")
        return
    
    print(f"Loaded results from: {data['timestamp']}")
    
    # Extract statistics
    stats = extract_stats(data)
    print(f"Found {len(stats)} strategies")
    
    # Create visualizations
    print("\nGenerating visualizations...")
    
    try:
        # 1. Token Throughput Comparison
        fig1 = plot_token_throughput_comparison(stats)
        fig1.savefig('strategy_token_throughput.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_token_throughput.png")
        
        # 2. Cache Performance
        fig2 = plot_cache_performance(stats)
        fig2.savefig('strategy_cache_performance.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_cache_performance.png")
        
        # 3. Speedup Factors
        fig3 = plot_speedup_factors(stats)
        fig3.savefig('strategy_speedup_factors.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_speedup_factors.png")
        
        # 4. Improvement Breakdown
        fig4 = plot_improvement_breakdown(stats)
        fig4.savefig('strategy_improvements.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_improvements.png")
        
        # 5. Latency Comparison
        fig5 = plot_latency_comparison(stats)
        fig5.savefig('strategy_latency_comparison.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_latency_comparison.png")
        
        # 6. Latency Breakdown
        fig6 = plot_latency_breakdown(stats)
        fig6.savefig('strategy_latency_breakdown.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_latency_breakdown.png")
        
        # 7. Normalizer Impact
        if len(stats) >= 3:
            fig7 = plot_normalizer_impact(stats)
            if fig7:
                fig7.savefig('normalizer_impact.png', dpi=300, bbox_inches='tight')
                print("   [SAVED] normalizer_impact.png")
        
        # 8. Summary Dashboard
        fig6 = create_summary_dashboard(stats)
        fig6.savefig('strategy_dashboard.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] strategy_dashboard.png")
        
        print("\nAll visualizations created successfully!")
        print("\nGenerated files:")
        print("  - strategy_token_throughput.png")
        print("  - strategy_cache_performance.png")
        print("  - strategy_speedup_factors.png")
        print("  - strategy_improvements.png")
        print("  - strategy_latency_comparison.png")
        print("  - strategy_latency_breakdown.png")
        print("  - normalizer_impact.png")
        print("  - strategy_dashboard.png")
        
        print("\nOpening visualizations...")
        plt.show()
        
    except Exception as e:
        print(f"\nError creating visualizations: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()


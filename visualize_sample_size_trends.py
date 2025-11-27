"""
Visualization script for multi-sample-size benchmark results.
Creates line plots showing how metrics change across different sample sizes.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


def load_results(filename: str = "cache_strategies_multiple_sizes.json") -> Dict:
    """Load benchmark results from JSON file."""
    if not Path(filename).exists():
        print(f"Error: {filename} not found.")
        print("Please run benchmark_multiple_sample_sizes.py first to generate results.")
        return None
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return data


def extract_metrics_by_sample_size(data: Dict) -> Dict:
    """Extract metrics organized by sample size."""
    metrics = {
        "sample_sizes": [],
        "strategies": {
            "No Cache": {
                "hit_rate": [],
                "throughput_aggregate": [],
                "throughput_per_query": [],
                "avg_latency": [],
                "total_tokens": [],
                "cache_hits": [],
                "cache_misses": [],
            },
            "LRU Cache (Basic)": {
                "hit_rate": [],
                "throughput_aggregate": [],
                "throughput_per_query": [],
                "avg_latency": [],
                "total_tokens": [],
                "cache_hits": [],
                "cache_misses": [],
            },
            "LRU Cache + Normalizer": {
                "hit_rate": [],
                "throughput_aggregate": [],
                "throughput_per_query": [],
                "avg_latency": [],
                "total_tokens": [],
                "cache_hits": [],
                "cache_misses": [],
            },
        }
    }
    
    for result in data["results"]:
        sample_size = result["sample_size"]
        metrics["sample_sizes"].append(sample_size)
        
        for strategy_name, stats in result["strategies"].items():
            if strategy_name in metrics["strategies"]:
                metrics["strategies"][strategy_name]["hit_rate"].append(stats["cache_hit_rate"])
                metrics["strategies"][strategy_name]["throughput_aggregate"].append(
                    stats["throughput_tokens_per_sec_aggregate"]
                )
                metrics["strategies"][strategy_name]["throughput_per_query"].append(
                    stats["avg_tokens_per_sec_per_query"]
                )
                metrics["strategies"][strategy_name]["avg_latency"].append(stats["avg_latency"])
                metrics["strategies"][strategy_name]["total_tokens"].append(stats["total_tokens_generated"])
                metrics["strategies"][strategy_name]["cache_hits"].append(stats["cache_hits"])
                metrics["strategies"][strategy_name]["cache_misses"].append(stats["cache_misses"])
    
    return metrics


def plot_token_throughput_trends(metrics: Dict):
    """Plot token throughput trends across sample sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Token Throughput Trends Across Sample Sizes', fontsize=16, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    colors = {'No Cache': '#e74c3c', 'LRU Cache (Basic)': '#f39c12', 'LRU Cache + Normalizer': '#2ecc71'}
    markers = {'No Cache': 'o', 'LRU Cache (Basic)': 's', 'LRU Cache + Normalizer': '^'}
    linestyles = {'No Cache': '--', 'LRU Cache (Basic)': '-', 'LRU Cache + Normalizer': '-'}
    
    # Plot 1: Aggregate Throughput
    ax = axes[0]
    for strategy_name in metrics["strategies"].keys():
        throughputs = metrics["strategies"][strategy_name]["throughput_aggregate"]
        ax.plot(sample_sizes, throughputs, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Aggregate Throughput (tokens/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Aggregate Token Throughput\n(Total Tokens / Total Time)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(sample_sizes)
    
    # Plot 2: Per-Query Throughput
    ax = axes[1]
    for strategy_name in metrics["strategies"].keys():
        throughputs = metrics["strategies"][strategy_name]["throughput_per_query"]
        ax.plot(sample_sizes, throughputs, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Per-Query Throughput (tokens/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Per-Query Token Throughput\n(Average tokens/sec per query)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(sample_sizes)
    
    plt.tight_layout()
    return fig


def plot_latency_trends(metrics: Dict):
    """Plot latency trends across sample sizes."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Latency Trends Across Sample Sizes', fontsize=16, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    colors = {'No Cache': '#e74c3c', 'LRU Cache (Basic)': '#f39c12', 'LRU Cache + Normalizer': '#2ecc71'}
    markers = {'No Cache': 'o', 'LRU Cache (Basic)': 's', 'LRU Cache + Normalizer': '^'}
    linestyles = {'No Cache': '--', 'LRU Cache (Basic)': '-', 'LRU Cache + Normalizer': '-'}
    
    # Plot 1: Average Latency
    ax = axes[0, 0]
    for strategy_name in metrics["strategies"].keys():
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        ax.plot(sample_sizes, latencies, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Latency (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Average Latency Trend', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(sample_sizes)
    
    # Plot 2: Latency Speedup
    ax = axes[0, 1]
    no_cache_latencies = metrics["strategies"]["No Cache"]["avg_latency"]
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        speedups = [no_lat / lat for no_lat, lat in zip(no_cache_latencies, latencies)]
        
        ax.plot(sample_sizes, speedups, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency Speedup (x)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Speedup vs No Cache', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Baseline (1.0x)')
    ax.set_xticks(sample_sizes)
    
    # Plot 3: Latency Reduction Percentage
    ax = axes[1, 0]
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        reductions = [((no_lat - lat) / no_lat * 100) if no_lat > 0 else 0 
                     for no_lat, lat in zip(no_cache_latencies, latencies)]
        
        ax.plot(sample_sizes, reductions, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
        ax.fill_between(sample_sizes, reductions, 0, alpha=0.2, color=colors[strategy_name])
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency Reduction (%)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Reduction vs No Cache', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(sample_sizes)
    
    # Plot 4: Latency Improvement from Normalizer
    ax = axes[1, 1]
    lru_basic_latencies = metrics["strategies"]["LRU Cache (Basic)"]["avg_latency"]
    lru_norm_latencies = metrics["strategies"]["LRU Cache + Normalizer"]["avg_latency"]
    improvements = [((basic - norm) / basic * 100) if basic > 0 else 0 
                   for basic, norm in zip(lru_basic_latencies, lru_norm_latencies)]
    
    ax.plot(sample_sizes, improvements, 
           color='#2ecc71', 
           marker='o',
           linewidth=3,
           markersize=10,
           label='Normalizer Improvement',
           alpha=0.9)
    ax.fill_between(sample_sizes, improvements, 0, alpha=0.2, color='#2ecc71')
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency Improvement (%)', fontsize=12, fontweight='bold')
    ax.set_title('Normalizer Latency Improvement\n(vs Basic LRU)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(sample_sizes)
    
    # Add value labels
    for size, improvement in zip(sample_sizes, improvements):
        ax.text(size, improvement, f'+{improvement:.1f}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    return fig


def plot_cache_performance_trends(metrics: Dict):
    """Plot cache performance trends across sample sizes."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Cache Performance Trends Across Sample Sizes', fontsize=16, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    colors = {'No Cache': '#e74c3c', 'LRU Cache (Basic)': '#f39c12', 'LRU Cache + Normalizer': '#2ecc71'}
    markers = {'No Cache': 'o', 'LRU Cache (Basic)': 's', 'LRU Cache + Normalizer': '^'}
    linestyles = {'No Cache': '--', 'LRU Cache (Basic)': '-', 'LRU Cache + Normalizer': '-'}
    
    # Plot 1: Hit Rate
    ax = axes[0]
    for strategy_name in metrics["strategies"].keys():
        hit_rates = metrics["strategies"][strategy_name]["hit_rate"]
        ax.plot(sample_sizes, hit_rates, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cache Hit Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Cache Hit Rate Trend', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim([0, 100])
    ax.set_xticks(sample_sizes)
    
    # Plot 2: Cache Hits
    ax = axes[1]
    for strategy_name in metrics["strategies"].keys():
        hits = metrics["strategies"][strategy_name]["cache_hits"]
        ax.plot(sample_sizes, hits, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Cache Hits', fontsize=12, fontweight='bold')
    ax.set_title('Cache Hits Trend', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(sample_sizes)
    
    # Plot 3: Average Latency
    ax = axes[2]
    for strategy_name in metrics["strategies"].keys():
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        ax.plot(sample_sizes, latencies, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linestyle=linestyles[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Latency (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Average Query Latency Trend', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xticks(sample_sizes)
    
    plt.tight_layout()
    return fig


def plot_speedup_trends(metrics: Dict):
    """Plot speedup trends across sample sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Performance Speedup Trends Across Sample Sizes', fontsize=16, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    no_cache_latencies = metrics["strategies"]["No Cache"]["avg_latency"]
    no_cache_throughputs = metrics["strategies"]["No Cache"]["throughput_aggregate"]
    
    colors = {'LRU Cache (Basic)': '#f39c12', 'LRU Cache + Normalizer': '#2ecc71'}
    markers = {'LRU Cache (Basic)': 's', 'LRU Cache + Normalizer': '^'}
    
    # Plot 1: Latency Speedup
    ax = axes[0]
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        speedups = [no_lat / lat for no_lat, lat in zip(no_cache_latencies, latencies)]
        
        ax.plot(sample_sizes, speedups, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency Speedup (x)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Speedup vs No Cache', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Baseline (1.0x)')
    ax.set_xticks(sample_sizes)
    
    # Plot 2: Throughput Speedup
    ax = axes[1]
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        throughputs = metrics["strategies"][strategy_name]["throughput_aggregate"]
        speedups = [tput / no_tput for tput, no_tput in zip(throughputs, no_cache_throughputs)]
        
        ax.plot(sample_sizes, speedups, 
               color=colors[strategy_name], 
               marker=markers[strategy_name],
               linewidth=2.5,
               markersize=8,
               label=strategy_name,
               alpha=0.9)
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Throughput Speedup (x)', fontsize=12, fontweight='bold')
    ax.set_title('Throughput Speedup vs No Cache', fontsize=12, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Baseline (1.0x)')
    ax.set_xticks(sample_sizes)
    
    plt.tight_layout()
    return fig


def plot_normalizer_impact_trend(metrics: Dict):
    """Plot how normalizer impact changes across sample sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Query Normalizer Impact Across Sample Sizes', fontsize=16, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    lru_basic_hit_rates = metrics["strategies"]["LRU Cache (Basic)"]["hit_rate"]
    lru_norm_hit_rates = metrics["strategies"]["LRU Cache + Normalizer"]["hit_rate"]
    lru_basic_throughputs = metrics["strategies"]["LRU Cache (Basic)"]["throughput_aggregate"]
    lru_norm_throughputs = metrics["strategies"]["LRU Cache + Normalizer"]["throughput_aggregate"]
    
    # Calculate improvements
    hit_rate_gains = [norm - basic for norm, basic in zip(lru_norm_hit_rates, lru_basic_hit_rates)]
    throughput_gains = [((norm - basic) / basic * 100) if basic > 0 else 0 
                       for norm, basic in zip(lru_norm_throughputs, lru_basic_throughputs)]
    
    # Plot 1: Hit Rate Gain
    ax = axes[0]
    ax.plot(sample_sizes, hit_rate_gains, 
           color='#2ecc71', 
           marker='o',
           linewidth=3,
           markersize=10,
           label='Hit Rate Gain',
           alpha=0.9)
    ax.fill_between(sample_sizes, hit_rate_gains, 0, alpha=0.2, color='#2ecc71')
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Hit Rate Gain (%)', fontsize=12, fontweight='bold')
    ax.set_title('Normalizer Hit Rate Improvement\n(vs Basic LRU)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(sample_sizes)
    
    # Add value labels
    for size, gain in zip(sample_sizes, hit_rate_gains):
        ax.text(size, gain, f'+{gain:.1f}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Plot 2: Throughput Gain
    ax = axes[1]
    ax.plot(sample_sizes, throughput_gains, 
           color='#2ecc71', 
           marker='o',
           linewidth=3,
           markersize=10,
           label='Throughput Gain',
           alpha=0.9)
    ax.fill_between(sample_sizes, throughput_gains, 0, alpha=0.2, color='#2ecc71')
    
    ax.set_xlabel('Sample Size (Number of Queries)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Throughput Gain (%)', fontsize=12, fontweight='bold')
    ax.set_title('Normalizer Throughput Improvement\n(vs Basic LRU)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(sample_sizes)
    
    # Add value labels
    for size, gain in zip(sample_sizes, throughput_gains):
        ax.text(size, gain, f'+{gain:.1f}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    return fig


def create_comprehensive_dashboard(metrics: Dict):
    """Create comprehensive dashboard with all trends."""
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
    
    fig.suptitle('Cache Strategy Performance Trends Across Sample Sizes', 
                 fontsize=18, fontweight='bold')
    
    sample_sizes = metrics["sample_sizes"]
    colors = {'No Cache': '#e74c3c', 'LRU Cache (Basic)': '#f39c12', 'LRU Cache + Normalizer': '#2ecc71'}
    markers = {'No Cache': 'o', 'LRU Cache (Basic)': 's', 'LRU Cache + Normalizer': '^'}
    linestyles = {'No Cache': '--', 'LRU Cache (Basic)': '-', 'LRU Cache + Normalizer': '-'}
    
    # 1. Aggregate Throughput
    ax1 = fig.add_subplot(gs[0, 0])
    for strategy_name in metrics["strategies"].keys():
        throughputs = metrics["strategies"][strategy_name]["throughput_aggregate"]
        ax1.plot(sample_sizes, throughputs, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax1.set_title('Aggregate Throughput\n(tokens/sec)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Sample Size', fontsize=10)
    ax1.set_ylabel('Tokens/sec', fontsize=10)
    ax1.legend(fontsize=9, loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(sample_sizes)
    
    # 2. Per-Query Throughput
    ax2 = fig.add_subplot(gs[0, 1])
    for strategy_name in metrics["strategies"].keys():
        throughputs = metrics["strategies"][strategy_name]["throughput_per_query"]
        ax2.plot(sample_sizes, throughputs, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax2.set_title('Per-Query Throughput\n(tokens/sec)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Sample Size', fontsize=10)
    ax2.set_ylabel('Tokens/sec', fontsize=10)
    ax2.legend(fontsize=9, loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(sample_sizes)
    
    # 3. Hit Rate
    ax3 = fig.add_subplot(gs[0, 2])
    for strategy_name in metrics["strategies"].keys():
        hit_rates = metrics["strategies"][strategy_name]["hit_rate"]
        ax3.plot(sample_sizes, hit_rates, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax3.set_title('Cache Hit Rate\n(%)', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Sample Size', fontsize=10)
    ax3.set_ylabel('Hit Rate %', fontsize=10)
    ax3.legend(fontsize=9, loc='best')
    ax3.set_ylim([0, 100])
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(sample_sizes)
    
    # 4. Average Latency
    ax4 = fig.add_subplot(gs[1, 0])
    for strategy_name in metrics["strategies"].keys():
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        ax4.plot(sample_sizes, latencies, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax4.set_title('Average Latency\n(seconds)', fontsize=11, fontweight='bold')
    ax4.set_xlabel('Sample Size', fontsize=10)
    ax4.set_ylabel('Latency (s)', fontsize=10)
    ax4.legend(fontsize=9, loc='best')
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(sample_sizes)
    
    # 5. Cache Hits
    ax5 = fig.add_subplot(gs[1, 1])
    for strategy_name in metrics["strategies"].keys():
        hits = metrics["strategies"][strategy_name]["cache_hits"]
        ax5.plot(sample_sizes, hits, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax5.set_title('Cache Hits\n(count)', fontsize=11, fontweight='bold')
    ax5.set_xlabel('Sample Size', fontsize=10)
    ax5.set_ylabel('Number of Hits', fontsize=10)
    ax5.legend(fontsize=9, loc='best')
    ax5.grid(True, alpha=0.3)
    ax5.set_xticks(sample_sizes)
    
    # 6. Total Tokens
    ax6 = fig.add_subplot(gs[1, 2])
    for strategy_name in metrics["strategies"].keys():
        tokens = metrics["strategies"][strategy_name]["total_tokens"]
        ax6.plot(sample_sizes, tokens, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linestyle=linestyles[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax6.set_title('Total Tokens\n(generated)', fontsize=11, fontweight='bold')
    ax6.set_xlabel('Sample Size', fontsize=10)
    ax6.set_ylabel('Total Tokens', fontsize=10)
    ax6.legend(fontsize=9, loc='best')
    ax6.grid(True, alpha=0.3)
    ax6.set_xticks(sample_sizes)
    
    # 7-9. Speedup and improvements
    no_cache_latencies = metrics["strategies"]["No Cache"]["avg_latency"]
    no_cache_throughputs = metrics["strategies"]["No Cache"]["throughput_aggregate"]
    
    # Latency Speedup
    ax7 = fig.add_subplot(gs[2, 0])
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        latencies = metrics["strategies"][strategy_name]["avg_latency"]
        speedups = [no_lat / lat for no_lat, lat in zip(no_cache_latencies, latencies)]
        ax7.plot(sample_sizes, speedups, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax7.set_title('Latency Speedup\n(vs No Cache)', fontsize=11, fontweight='bold')
    ax7.set_xlabel('Sample Size', fontsize=10)
    ax7.set_ylabel('Speedup (x)', fontsize=10)
    ax7.legend(fontsize=9, loc='best')
    ax7.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
    ax7.grid(True, alpha=0.3)
    ax7.set_xticks(sample_sizes)
    
    # Throughput Speedup
    ax8 = fig.add_subplot(gs[2, 1])
    for strategy_name in ["LRU Cache (Basic)", "LRU Cache + Normalizer"]:
        throughputs = metrics["strategies"][strategy_name]["throughput_aggregate"]
        speedups = [tput / no_tput for tput, no_tput in zip(throughputs, no_cache_throughputs)]
        ax8.plot(sample_sizes, speedups, 
                color=colors[strategy_name], 
                marker=markers[strategy_name],
                linewidth=2,
                markersize=6,
                label=strategy_name,
                alpha=0.9)
    ax8.set_title('Throughput Speedup\n(vs No Cache)', fontsize=11, fontweight='bold')
    ax8.set_xlabel('Sample Size', fontsize=10)
    ax8.set_ylabel('Speedup (x)', fontsize=10)
    ax8.legend(fontsize=9, loc='best')
    ax8.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
    ax8.grid(True, alpha=0.3)
    ax8.set_xticks(sample_sizes)
    
    # Normalizer Impact
    ax9 = fig.add_subplot(gs[2, 2])
    lru_basic_hit_rates = metrics["strategies"]["LRU Cache (Basic)"]["hit_rate"]
    lru_norm_hit_rates = metrics["strategies"]["LRU Cache + Normalizer"]["hit_rate"]
    hit_rate_gains = [norm - basic for norm, basic in zip(lru_norm_hit_rates, lru_basic_hit_rates)]
    ax9.plot(sample_sizes, hit_rate_gains, 
            color='#2ecc71', 
            marker='o',
            linewidth=2.5,
            markersize=8,
            label='Normalizer Gain',
            alpha=0.9)
    ax9.fill_between(sample_sizes, hit_rate_gains, 0, alpha=0.2, color='#2ecc71')
    ax9.set_title('Normalizer Impact\n(Hit Rate Gain)', fontsize=11, fontweight='bold')
    ax9.set_xlabel('Sample Size', fontsize=10)
    ax9.set_ylabel('Gain (%)', fontsize=10)
    ax9.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax9.grid(True, alpha=0.3)
    ax9.set_xticks(sample_sizes)
    
    return fig


def main():
    """Main visualization function."""
    print("="*80)
    print("CACHE STRATEGY TRENDS VISUALIZATION")
    print("="*80)
    
    # Load results
    data = load_results("cache_strategies_multiple_sizes.json")
    if not data:
        print("\nNo results found. Run benchmark first:")
        print("  python benchmark_multiple_sample_sizes.py")
        return
    
    print(f"Loaded results from: {data['timestamp']}")
    print(f"Sample sizes tested: {data['sample_sizes']}")
    
    # Extract metrics
    metrics = extract_metrics_by_sample_size(data)
    print(f"Extracted metrics for {len(metrics['sample_sizes'])} sample sizes")
    
    # Create visualizations
    print("\nGenerating visualizations...")
    
    try:
        # 1. Token Throughput Trends
        fig1 = plot_token_throughput_trends(metrics)
        fig1.savefig('sample_size_token_throughput_trends.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_token_throughput_trends.png")
        
        # 2. Latency Trends
        fig2 = plot_latency_trends(metrics)
        fig2.savefig('sample_size_latency_trends.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_latency_trends.png")
        
        # 3. Cache Performance Trends
        fig3 = plot_cache_performance_trends(metrics)
        fig3.savefig('sample_size_cache_performance_trends.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_cache_performance_trends.png")
        
        # 4. Speedup Trends
        fig4 = plot_speedup_trends(metrics)
        fig4.savefig('sample_size_speedup_trends.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_speedup_trends.png")
        
        # 5. Normalizer Impact Trend
        fig4 = plot_normalizer_impact_trend(metrics)
        fig4.savefig('sample_size_normalizer_impact_trend.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_normalizer_impact_trend.png")
        
        # 5. Comprehensive Dashboard
        fig5 = create_comprehensive_dashboard(metrics)
        fig5.savefig('sample_size_comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
        print("   [SAVED] sample_size_comprehensive_dashboard.png")
        
        print("\nAll visualizations created successfully!")
        print("\nGenerated files:")
        print("  - sample_size_token_throughput_trends.png")
        print("  - sample_size_latency_trends.png")
        print("  - sample_size_cache_performance_trends.png")
        print("  - sample_size_speedup_trends.png")
        print("  - sample_size_normalizer_impact_trend.png")
        print("  - sample_size_comprehensive_dashboard.png")
        
        print("\nOpening visualizations...")
        plt.show()
        
    except Exception as e:
        print(f"\nError creating visualizations: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()


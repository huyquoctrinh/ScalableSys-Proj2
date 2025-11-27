"""
Visualization script for benchmark results.
Creates charts comparing cache performance metrics.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List


def load_benchmark_results(filename: str = "benchmark_results.json") -> Dict:
    """Load benchmark results from JSON file."""
    if not Path(filename).exists():
        print(f"❌ Error: {filename} not found.")
        print("Please run benchmark_cache_performance.py first to generate results.")
        return None
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return data


def parse_results(data: Dict) -> tuple:
    """Parse benchmark data into separate lists for with/without cache."""
    with_lru = []
    without_cache = []
    
    for result in data['results']:
        if 'With LRU' in result['name']:
            with_lru.append(result)
        elif 'Without' in result['name']:
            without_cache.append(result)
    
    # Sort by sample size
    with_lru.sort(key=lambda x: x['sample_size'])
    without_cache.sort(key=lambda x: x['sample_size'])
    
    return with_lru, without_cache


def plot_latency_comparison(with_lru: List[Dict], without_cache: List[Dict]):
    """Plot latency comparison charts."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Latency Comparison: With LRU Cache vs Without Cache', fontsize=16, fontweight='bold')
    
    sample_sizes = [r['sample_size'] for r in with_lru]
    
    # Average Latency
    ax = axes[0, 0]
    lru_avg = [r['avg_latency'] for r in with_lru]
    no_cache_avg = [r['avg_latency'] for r in without_cache]
    
    x = np.arange(len(sample_sizes))
    width = 0.35
    
    ax.bar(x - width/2, lru_avg, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_avg, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Latency (seconds)')
    ax.set_title('Average Latency')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Median Latency
    ax = axes[0, 1]
    lru_med = [r['median_latency'] for r in with_lru]
    no_cache_med = [r['median_latency'] for r in without_cache]
    
    ax.bar(x - width/2, lru_med, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_med, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Latency (seconds)')
    ax.set_title('Median Latency')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # P95 Latency
    ax = axes[1, 0]
    lru_p95 = [r['p95_latency'] for r in with_lru]
    no_cache_p95 = [r['p95_latency'] for r in without_cache]
    
    ax.bar(x - width/2, lru_p95, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_p95, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Latency (seconds)')
    ax.set_title('P95 Latency')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Latency Improvement %
    ax = axes[1, 1]
    improvements = [(no_cache_avg[i] - lru_avg[i]) / no_cache_avg[i] * 100 
                   for i in range(len(sample_sizes))]
    
    bars = ax.bar(x, improvements, color='#3498db')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Latency Improvement with LRU Cache')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    return fig


def plot_throughput_comparison(with_lru: List[Dict], without_cache: List[Dict]):
    """Plot throughput comparison charts (queries/sec and tokens/sec)."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Throughput Comparison: With LRU Cache vs Without Cache', fontsize=16, fontweight='bold')
    
    sample_sizes = [r['sample_size'] for r in with_lru]
    x = np.arange(len(sample_sizes))
    width = 0.35
    
    # Query Throughput (queries/sec)
    ax = axes[0, 0]
    lru_throughput_q = [r['throughput_queries'] for r in with_lru]
    no_cache_throughput_q = [r['throughput_queries'] for r in without_cache]
    
    ax.bar(x - width/2, lru_throughput_q, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_throughput_q, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Queries per Second')
    ax.set_title('Query Throughput')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Token Throughput (tokens/sec)
    ax = axes[0, 1]
    lru_throughput_t = [r['throughput_tokens'] for r in with_lru]
    no_cache_throughput_t = [r['throughput_tokens'] for r in without_cache]
    
    ax.bar(x - width/2, lru_throughput_t, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_throughput_t, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Tokens per Second')
    ax.set_title('Token Throughput (LLM Performance)')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Query Throughput Improvement %
    ax = axes[1, 0]
    improvements_q = [(lru_throughput_q[i] - no_cache_throughput_q[i]) / no_cache_throughput_q[i] * 100 
                     for i in range(len(sample_sizes))]
    
    bars = ax.bar(x, improvements_q, color='#3498db')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Query Throughput Improvement')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # Token Throughput Improvement %
    ax = axes[1, 1]
    improvements_t = [(lru_throughput_t[i] - no_cache_throughput_t[i]) / no_cache_throughput_t[i] * 100 
                     for i in range(len(sample_sizes))]
    
    bars = ax.bar(x, improvements_t, color='#9b59b6')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Token Throughput Improvement')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    return fig


def plot_speedup_factor(with_lru: List[Dict], without_cache: List[Dict]):
    """Plot speedup factor across different sample sizes."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sample_sizes = [r['sample_size'] for r in with_lru]
    speedups = [without_cache[i]['avg_latency'] / with_lru[i]['avg_latency'] 
                for i in range(len(sample_sizes))]
    
    # Line plot with markers
    ax.plot(sample_sizes, speedups, marker='o', linewidth=2, markersize=10, 
            color='#3498db', label='Speedup Factor')
    
    # Add baseline
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, label='No Improvement (1.0x)')
    
    ax.set_xlabel('Sample Size', fontsize=12)
    ax.set_ylabel('Speedup Factor (x)', fontsize=12)
    ax.set_title('Cache Speedup Factor vs Sample Size', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add value labels
    for i, (size, speedup) in enumerate(zip(sample_sizes, speedups)):
        ax.text(size, speedup + 0.1, f'{speedup:.2f}x', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return fig


def plot_total_time_comparison(with_lru: List[Dict], without_cache: List[Dict]):
    """Plot total execution time comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Total Execution Time Comparison', fontsize=16, fontweight='bold')
    
    sample_sizes = [r['sample_size'] for r in with_lru]
    x = np.arange(len(sample_sizes))
    width = 0.35
    
    # Total Time
    ax = axes[0]
    lru_time = [r['total_time'] for r in with_lru]
    no_cache_time = [r['total_time'] for r in without_cache]
    
    ax.bar(x - width/2, lru_time, width, label='With LRU Cache', color='#2ecc71')
    ax.bar(x + width/2, no_cache_time, width, label='Without Cache', color='#e74c3c')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('Total Execution Time')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Time Saved
    ax = axes[1]
    time_saved = [no_cache_time[i] - lru_time[i] for i in range(len(sample_sizes))]
    time_saved_pct = [(no_cache_time[i] - lru_time[i]) / no_cache_time[i] * 100 
                      for i in range(len(sample_sizes))]
    
    bars = ax.bar(x, time_saved, color='#9b59b6')
    ax.set_xlabel('Sample Size')
    ax.set_ylabel('Time Saved (seconds)')
    ax.set_title('Time Saved with LRU Cache')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_sizes)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels with percentage
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s\n({time_saved_pct[i]:.1f}%)', 
                ha='center', va='bottom')
    
    plt.tight_layout()
    return fig


def create_summary_dashboard(with_lru: List[Dict], without_cache: List[Dict]):
    """Create a comprehensive summary dashboard."""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle('Cache Performance Dashboard', fontsize=18, fontweight='bold')
    
    sample_sizes = [r['sample_size'] for r in with_lru]
    x = np.arange(len(sample_sizes))
    
    # 1. Average Latency
    ax1 = fig.add_subplot(gs[0, 0])
    lru_avg = [r['avg_latency'] for r in with_lru]
    no_cache_avg = [r['avg_latency'] for r in without_cache]
    ax1.plot(sample_sizes, lru_avg, marker='o', label='With LRU', color='#2ecc71')
    ax1.plot(sample_sizes, no_cache_avg, marker='s', label='Without', color='#e74c3c')
    ax1.set_title('Average Latency')
    ax1.set_xlabel('Sample Size')
    ax1.set_ylabel('Seconds')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Query Throughput
    ax2 = fig.add_subplot(gs[0, 1])
    lru_throughput_q = [r['throughput_queries'] for r in with_lru]
    no_cache_throughput_q = [r['throughput_queries'] for r in without_cache]
    ax2.plot(sample_sizes, lru_throughput_q, marker='o', label='With LRU', color='#2ecc71')
    ax2.plot(sample_sizes, no_cache_throughput_q, marker='s', label='Without', color='#e74c3c')
    ax2.set_title('Query Throughput')
    ax2.set_xlabel('Sample Size')
    ax2.set_ylabel('Queries/sec')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Token Throughput
    ax3 = fig.add_subplot(gs[0, 2])
    lru_throughput_t = [r['throughput_tokens'] for r in with_lru]
    no_cache_throughput_t = [r['throughput_tokens'] for r in without_cache]
    ax3.plot(sample_sizes, lru_throughput_t, marker='o', label='With LRU', color='#2ecc71')
    ax3.plot(sample_sizes, no_cache_throughput_t, marker='s', label='Without', color='#e74c3c')
    ax3.set_title('Token Throughput (LLM)')
    ax3.set_xlabel('Sample Size')
    ax3.set_ylabel('Tokens/sec')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Speedup Factor
    ax4 = fig.add_subplot(gs[1, 0])
    speedups = [no_cache_avg[i] / lru_avg[i] for i in range(len(sample_sizes))]
    ax4.plot(sample_sizes, speedups, marker='D', linewidth=2, color='#3498db')
    ax4.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
    ax4.set_title('Speedup Factor')
    ax4.set_xlabel('Sample Size')
    ax4.set_ylabel('Speedup (x)')
    ax4.grid(True, alpha=0.3)
    
    # 5. Latency Distribution (for largest sample)
    ax5 = fig.add_subplot(gs[1, 1:3])
    largest_idx = -1  # Last (largest) sample
    metrics = ['Avg', 'Median', 'Min', 'Max', 'P95']
    lru_vals = [
        with_lru[largest_idx]['avg_latency'],
        with_lru[largest_idx]['median_latency'],
        with_lru[largest_idx]['min_latency'],
        with_lru[largest_idx]['max_latency'],
        with_lru[largest_idx]['p95_latency'],
    ]
    no_cache_vals = [
        without_cache[largest_idx]['avg_latency'],
        without_cache[largest_idx]['median_latency'],
        without_cache[largest_idx]['min_latency'],
        without_cache[largest_idx]['max_latency'],
        without_cache[largest_idx]['p95_latency'],
    ]
    
    x_pos = np.arange(len(metrics))
    width = 0.35
    ax5.bar(x_pos - width/2, lru_vals, width, label='With LRU', color='#2ecc71')
    ax5.bar(x_pos + width/2, no_cache_vals, width, label='Without', color='#e74c3c')
    ax5.set_title(f'Latency Distribution (n={with_lru[largest_idx]["sample_size"]})')
    ax5.set_ylabel('Seconds')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(metrics)
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)
    
    # 6. Cache Hit Rate
    ax6 = fig.add_subplot(gs[2, 0])
    cache_hit_rates = [r['cache_hit_rate'] for r in with_lru]
    ax6.bar(x, cache_hit_rates, color='#f39c12')
    ax6.set_title('Cache Hit Rate')
    ax6.set_xlabel('Sample Size')
    ax6.set_ylabel('Hit Rate (%)')
    ax6.set_xticks(x)
    ax6.set_xticklabels(sample_sizes)
    ax6.grid(axis='y', alpha=0.3)
    ax6.set_ylim([0, 100])
    
    # 7. Time Saved
    ax7 = fig.add_subplot(gs[2, 1])
    time_saved = [without_cache[i]['total_time'] - with_lru[i]['total_time'] 
                  for i in range(len(sample_sizes))]
    ax7.bar(x, time_saved, color='#9b59b6')
    ax7.set_title('Time Saved')
    ax7.set_xlabel('Sample Size')
    ax7.set_ylabel('Seconds')
    ax7.set_xticks(x)
    ax7.set_xticklabels(sample_sizes)
    ax7.grid(axis='y', alpha=0.3)
    
    # 8. Token Metrics
    ax8 = fig.add_subplot(gs[2, 2])
    lru_tokens = [r['total_tokens'] for r in with_lru]
    no_cache_tokens = [r['total_tokens'] for r in without_cache]
    ax8.bar(x - width/2, lru_tokens, width, label='With LRU', color='#2ecc71')
    ax8.bar(x + width/2, no_cache_tokens, width, label='Without', color='#e74c3c')
    ax8.set_title('Total Tokens Generated')
    ax8.set_xlabel('Sample Size')
    ax8.set_ylabel('Tokens')
    ax8.set_xticks(x)
    ax8.set_xticklabels(sample_sizes)
    ax8.legend()
    ax8.grid(axis='y', alpha=0.3)
    
    # 9. Improvement Summary Table
    ax9 = fig.add_subplot(gs[3, :])
    ax9.axis('off')
    
    table_data = []
    table_data.append(['Sample\nSize', 'Cache\nHit Rate', 'Latency\nImprovement', 
                      'Token\nThroughput', 'Speedup\nFactor', 'Time\nSaved (s)'])
    
    for i in range(len(sample_sizes)):
        hit_rate = with_lru[i]['cache_hit_rate']
        lat_imp = (no_cache_avg[i] - lru_avg[i]) / no_cache_avg[i] * 100
        tok_thr_imp = (lru_throughput_t[i] - no_cache_throughput_t[i]) / no_cache_throughput_t[i] * 100
        speedup = no_cache_avg[i] / lru_avg[i]
        time_s = without_cache[i]['total_time'] - with_lru[i]['total_time']
        
        table_data.append([
            str(sample_sizes[i]),
            f'{hit_rate:.1f}%',
            f'{lat_imp:.1f}%',
            f'{tok_thr_imp:.1f}%',
            f'{speedup:.2f}x',
            f'{time_s:.1f}s',
        ])
    
    table = ax9.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.12, 0.15, 0.18, 0.18, 0.18, 0.19])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header row
    for i in range(6):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(table_data)):
        color = '#ecf0f1' if i % 2 == 0 else 'white'
        for j in range(6):
            table[(i, j)].set_facecolor(color)
    
    return fig


def main():
    """Main visualization function."""
    print("="*70)
    print("📊 BENCHMARK VISUALIZATION")
    print("="*70)
    
    # Try loading from multiple possible files
    data = None
    for filename in ["benchmark_results.json", "quick_benchmark_results.json"]:
        data = load_benchmark_results(filename)
        if data:
            print(f"✅ Loaded results from {filename}")
            break
    
    if not data:
        print("\n❌ No benchmark results found.")
        print("Run one of these commands first:")
        print("  python benchmark_cache_performance.py")
        print("  python benchmark_cache_quick.py")
        return
    
    print(f"📅 Results from: {data['timestamp']}")
    
    # Parse results
    with_lru, without_cache = parse_results(data)
    
    if not with_lru or not without_cache:
        print("❌ Error: Could not parse benchmark results properly.")
        return
    
    print(f"📈 Found {len(with_lru)} sample size comparisons")
    
    # Create visualizations
    print("\n🎨 Generating visualizations...")
    
    try:
        # Latency comparison
        fig1 = plot_latency_comparison(with_lru, without_cache)
        fig1.savefig('latency_comparison.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: latency_comparison.png")
        
        # Throughput comparison
        fig2 = plot_throughput_comparison(with_lru, without_cache)
        fig2.savefig('throughput_comparison.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: throughput_comparison.png")
        
        # Speedup factor
        fig3 = plot_speedup_factor(with_lru, without_cache)
        fig3.savefig('speedup_factor.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: speedup_factor.png")
        
        # Total time comparison
        fig4 = plot_total_time_comparison(with_lru, without_cache)
        fig4.savefig('time_comparison.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: time_comparison.png")
        
        # Summary dashboard
        fig5 = create_summary_dashboard(with_lru, without_cache)
        fig5.savefig('performance_dashboard.png', dpi=300, bbox_inches='tight')
        print("   ✅ Saved: performance_dashboard.png")
        
        print("\n✅ All visualizations created successfully!")
        print("\n📁 Generated files:")
        print("   - latency_comparison.png")
        print("   - throughput_comparison.png")
        print("   - speedup_factor.png")
        print("   - time_comparison.png")
        print("   - performance_dashboard.png")
        
        print("\n🔍 Opening visualizations...")
        plt.show()
        
    except Exception as e:
        print(f"\n❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()


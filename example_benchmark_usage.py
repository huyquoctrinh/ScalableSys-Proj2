"""
Example script demonstrating how to use the benchmark tools.
This script shows how to run custom benchmarks and analyze results.
"""

import json
from benchmark_cache_performance import (
    BenchmarkResult,
    generate_test_questions,
)


def example_1_basic_usage():
    """Example 1: Basic benchmark usage."""
    print("="*70)
    print("Example 1: Running a basic benchmark")
    print("="*70)
    print("\nTo run a quick benchmark with default settings:")
    print("  python benchmark_cache_quick.py")
    print("\nThis will:")
    print("  - Test with 10, 20, 30 queries")
    print("  - Compare WITH vs WITHOUT LRU cache")
    print("  - Print results to console")
    print("  - Save results to quick_benchmark_results.json")


def example_2_custom_questions():
    """Example 2: How to add custom test questions."""
    print("\n" + "="*70)
    print("Example 2: Adding custom test questions")
    print("="*70)
    
    # Example custom questions
    custom_questions = [
        "Who won the Nobel Prize in Literature in 2023?",
        "List all Nobel laureates from Japan.",
        "How many Nobel Prizes were awarded in Medicine?",
        "Which institution has the most Nobel laureates?",
        "Who is the oldest Nobel Prize winner?",
    ]
    
    print("\n1. Open benchmark_cache_quick.py or benchmark_cache_performance.py")
    print("2. Find the 'base_questions' list")
    print("3. Replace or add your questions:")
    print("\nbase_questions = [")
    for q in custom_questions:
        print(f'    "{q}",')
    print("]")
    print("\n4. Run the benchmark script")


def example_3_generate_test_set():
    """Example 3: Generate test questions with repetitions."""
    print("\n" + "="*70)
    print("Example 3: Generating test sets with repetitions")
    print("="*70)
    
    base_questions = [
        "Question 1",
        "Question 2",
        "Question 3",
    ]
    
    # Generate 10 questions with repetitions (simulates cache hits)
    test_set = generate_test_questions(base_questions, repeat_factor=2)[:10]
    
    print(f"\nBase questions: {len(base_questions)}")
    print(f"Generated test set: {len(test_set)} queries")
    print("\nTest set (with repetitions for cache testing):")
    for i, q in enumerate(test_set, 1):
        print(f"  {i}. {q}")
    
    print("\nNote: Repetitions simulate real-world cache hits!")


def example_4_analyze_results():
    """Example 4: How to analyze benchmark results."""
    print("\n" + "="*70)
    print("Example 4: Analyzing benchmark results")
    print("="*70)
    
    # Example result data
    example_result = {
        "name": "With LRU Cache (n=40)",
        "sample_size": 40,
        "avg_latency": 2.145,
        "median_latency": 1.832,
        "throughput": 0.466,
        "total_time": 85.800,
        "p95_latency": 4.321,
    }
    
    print("\nResults are saved in JSON format:")
    print(json.dumps(example_result, indent=2))
    
    print("\nKey metrics to look at:")
    print("  1. avg_latency: Lower is better")
    print("  2. throughput: Higher is better")
    print("  3. total_time: How long the benchmark took")
    print("  4. p95_latency: 95% of queries are faster than this")


def example_5_visualizations():
    """Example 5: Creating visualizations."""
    print("\n" + "="*70)
    print("Example 5: Creating visualizations")
    print("="*70)
    
    print("\nAfter running a benchmark:")
    print("  python benchmark_cache_quick.py")
    print("\nGenerate visualizations:")
    print("  python visualize_benchmark.py")
    print("\nThis creates PNG files:")
    print("  - latency_comparison.png")
    print("  - throughput_comparison.png")
    print("  - speedup_factor.png")
    print("  - time_comparison.png")
    print("  - performance_dashboard.png")


def example_6_comparing_cache_sizes():
    """Example 6: Comparing different cache sizes."""
    print("\n" + "="*70)
    print("Example 6: Testing different cache sizes")
    print("="*70)
    
    cache_sizes = [32, 64, 128, 256]
    
    print("\nTo test different cache sizes:")
    print("1. Modify the cache size in the benchmark script:")
    print("\nFor cache_size in [32, 64, 128, 256]:")
    print("    lru_cache_manager = LRUDataManager(cache_size=cache_size)")
    print("    # Run benchmark")
    print("    # Compare results")
    
    print("\nExpected behavior:")
    print("  - Larger cache = Higher hit rate")
    print("  - Larger cache = Better latency")
    print("  - Diminishing returns after certain size")


def example_7_understanding_speedup():
    """Example 7: Understanding speedup calculations."""
    print("\n" + "="*70)
    print("Example 7: Understanding speedup factor")
    print("="*70)
    
    # Example calculation
    no_cache_latency = 5.234
    with_cache_latency = 2.145
    speedup = no_cache_latency / with_cache_latency
    improvement_pct = ((no_cache_latency - with_cache_latency) / no_cache_latency) * 100
    
    print(f"\nGiven:")
    print(f"  Average latency WITHOUT cache: {no_cache_latency}s")
    print(f"  Average latency WITH cache:    {with_cache_latency}s")
    
    print(f"\nCalculations:")
    print(f"  Speedup factor = {no_cache_latency} / {with_cache_latency}")
    print(f"                 = {speedup:.2f}x faster")
    
    print(f"\n  Improvement % = ({no_cache_latency} - {with_cache_latency}) / {no_cache_latency} × 100")
    print(f"                = {improvement_pct:.1f}% faster")
    
    print("\nInterpretation:")
    if speedup >= 2.5:
        print(f"  ✅ Excellent! {speedup:.2f}x speedup is great cache performance")
    elif speedup >= 1.5:
        print(f"  ✓ Good! {speedup:.2f}x speedup shows effective caching")
    else:
        print(f"  ⚠ Moderate. {speedup:.2f}x speedup - consider cache optimization")


def example_8_cost_analysis():
    """Example 8: Estimating cost savings."""
    print("\n" + "="*70)
    print("Example 8: Cost analysis")
    print("="*70)
    
    # Example numbers
    total_queries = 100
    cache_hits = 65
    cache_misses = 35
    cost_per_llm_call = 0.002  # $0.002 per query
    
    print(f"\nScenario:")
    print(f"  Total queries:     {total_queries}")
    print(f"  Cache hits:        {cache_hits} ({cache_hits/total_queries*100:.0f}%)")
    print(f"  Cache misses:      {cache_misses} ({cache_misses/total_queries*100:.0f}%)")
    print(f"  Cost per LLM call: ${cost_per_llm_call}")
    
    cost_without_cache = total_queries * cost_per_llm_call
    cost_with_cache = cache_misses * cost_per_llm_call
    savings = cost_without_cache - cost_with_cache
    
    print(f"\nCost Analysis:")
    print(f"  Without cache: {total_queries} × ${cost_per_llm_call} = ${cost_without_cache:.2f}")
    print(f"  With cache:    {cache_misses} × ${cost_per_llm_call} = ${cost_with_cache:.2f}")
    print(f"  💰 Savings:    ${savings:.2f} ({savings/cost_without_cache*100:.0f}%)")
    
    print(f"\nScaled to 10,000 queries:")
    scaled_savings = savings * 100
    print(f"  Estimated savings: ${scaled_savings:.2f}")


def main():
    """Run all examples."""
    print("\n" + "🎓 BENCHMARK USAGE EXAMPLES" + "\n")
    print("This script demonstrates how to use the cache benchmarking tools.\n")
    
    # Run all examples
    example_1_basic_usage()
    example_2_custom_questions()
    example_3_generate_test_set()
    example_4_analyze_results()
    example_5_visualizations()
    example_6_comparing_cache_sizes()
    example_7_understanding_speedup()
    example_8_cost_analysis()
    
    print("\n" + "="*70)
    print("✅ Examples completed!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run: python benchmark_cache_quick.py")
    print("  2. Review the printed results")
    print("  3. Run: python visualize_benchmark.py")
    print("  4. Review the generated PNG charts")
    print("  5. Read: BENCHMARK_CACHE_GUIDE.md for details")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()


"""
Quick benchmark script for fast cache performance testing.
Tests with smaller sample sizes for rapid iteration.
"""

import os
import json
import kuzu
import dspy
import time
import statistics
from typing import Dict, List
from dotenv import load_dotenv
from text_2_cypher import (
    ExemplarSelector,
    QueryGenerator,
    CypherPostProcessor,
)
from cache_method import LRUDataManager
from graph_rag_workflow import (
    setup_llm,
    get_schema_dict,
    PruneSchema,
    AnswerQuestion,
    Text2Cypher,
)
from benchmark_cache_performance import (
    NoCacheManager,
    BenchmarkResult,
    process_question_benchmark,
    run_benchmark,
    generate_test_questions,
)


def print_quick_comparison(lru_stats: Dict, no_cache_stats: Dict, sample_size: int):
    """Print a concise comparison report."""
    print(f"\n{'='*70}")
    print(f"📊 QUICK BENCHMARK RESULTS (n={sample_size})")
    print(f"{'='*70}")
    
    # Latency comparison
    print(f"\n⏱️  LATENCY (seconds)")
    print(f"{'-'*70}")
    print(f"{'Metric':<20} {'With LRU':<15} {'Without':<15} {'Improvement':<15}")
    print(f"{'-'*70}")
    
    avg_improvement = ((no_cache_stats['avg_latency'] - lru_stats['avg_latency']) / 
                      no_cache_stats['avg_latency'] * 100)
    print(f"{'Average':<20} {lru_stats['avg_latency']:<15.3f} "
          f"{no_cache_stats['avg_latency']:<15.3f} {avg_improvement:>13.1f}%")
    
    print(f"{'Min':<20} {lru_stats['min_latency']:<15.3f} "
          f"{no_cache_stats['min_latency']:<15.3f}")
    
    print(f"{'Max':<20} {lru_stats['max_latency']:<15.3f} "
          f"{no_cache_stats['max_latency']:<15.3f}")
    
    # Throughput comparison
    print(f"\n⚡ THROUGHPUT")
    print(f"{'-'*70}")
    throughput_improvement = ((lru_stats['throughput'] - no_cache_stats['throughput']) / 
                             no_cache_stats['throughput'] * 100)
    print(f"With LRU:    {lru_stats['throughput']:.3f} queries/sec")
    print(f"Without:     {no_cache_stats['throughput']:.3f} queries/sec")
    print(f"Improvement: {throughput_improvement:+.1f}%")
    
    # Speedup
    print(f"\n🚀 SPEEDUP")
    print(f"{'-'*70}")
    speedup = no_cache_stats['avg_latency'] / lru_stats['avg_latency']
    print(f"Cached queries are {speedup:.2f}x faster")
    
    # Time saved
    time_saved = no_cache_stats['total_time'] - lru_stats['total_time']
    print(f"\n💾 TIME SAVED")
    print(f"{'-'*70}")
    print(f"Total time with LRU: {lru_stats['total_time']:.2f}s")
    print(f"Total time without:  {no_cache_stats['total_time']:.2f}s")
    print(f"Time saved:          {time_saved:.2f}s ({time_saved/no_cache_stats['total_time']*100:.1f}%)")
    
    print(f"\n{'='*70}\n")


def main():
    """Main quick benchmark execution."""
    print("="*70)
    print("⚡ QUICK CACHE PERFORMANCE BENCHMARK")
    print("="*70)
    print("Fast testing with smaller sample sizes\n")
    
    # === 1. Setup ===
    print("📦 Setting up...")
    lm = setup_llm()
    if not lm:
        return
    
    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name, read_only=True)
    conn = kuzu.Connection(db)
    
    # Load exemplars
    try:
        with open('exemplars.json', 'r') as f:
            exemplars = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error: {e}")
        return
    
    exemplar_selector = ExemplarSelector(exemplars=exemplars)
    post_processor = CypherPostProcessor()
    text2cypher_predictor = dspy.ChainOfThought(Text2Cypher)
    query_generator = QueryGenerator(conn=conn, text2cypher_predictor=text2cypher_predictor)
    prune_module = dspy.ChainOfThought(PruneSchema)
    answer_generator_module = dspy.ChainOfThought(AnswerQuestion)
    
    print("✅ Setup completed!\n")
    
    # === 2. Define Test Questions ===
    base_questions = [
        "Who won the Nobel Prize in Physics in 2020?",
        "How many Nobel Prizes were awarded in Chemistry?",
        "List all Nobel laureates from the United States.",
        "Which country has the most Nobel Prize winners?",
        "Who won the Nobel Peace Prize in 1964?",
        "How many women have won the Nobel Prize in Physics?",
        "What is the total number of Nobel Prize categories?",
        "Who was the youngest Nobel laureate?",
        "List all Nobel laureates affiliated with MIT.",
        "Which city has the most Nobel Prize winners?",
    ]
    
    # === 3. Quick Test with Small Sample Sizes ===
    sample_sizes = [10, 20, 30]  # Smaller sizes for quick testing
    
    print(f"📋 Configuration:")
    print(f"   Base questions: {len(base_questions)}")
    print(f"   Sample sizes: {sample_sizes}")
    print(f"   Cache size: 128 entries\n")
    
    all_results = []
    
    for sample_size in sample_sizes:
        print(f"\n{'#'*70}")
        print(f"Testing with {sample_size} queries")
        print(f"{'#'*70}\n")
        
        # Generate test questions
        repeat_factor = (sample_size // len(base_questions)) + 1
        test_questions = generate_test_questions(base_questions, repeat_factor)[:sample_size]
        
        # Test WITH LRU Cache
        print(f"🔄 Running WITH LRU cache...")
        lru_cache_manager = LRUDataManager(cache_size=128)
        lru_result = run_benchmark(
            questions=test_questions,
            conn=conn,
            prune_module=prune_module,
            cache_manager=lru_cache_manager,
            exemplar_selector=exemplar_selector,
            query_generator=query_generator,
            post_processor=post_processor,
            answer_generator_module=answer_generator_module,
            benchmark_name=f"With LRU (n={sample_size})",
        )
        lru_stats = lru_result.compute_stats()
        
        time.sleep(1)
        
        # Test WITHOUT Cache
        print(f"🔄 Running WITHOUT cache...")
        no_cache_manager = NoCacheManager()
        no_cache_result = run_benchmark(
            questions=test_questions,
            conn=conn,
            prune_module=prune_module,
            cache_manager=no_cache_manager,
            exemplar_selector=exemplar_selector,
            query_generator=query_generator,
            post_processor=post_processor,
            answer_generator_module=answer_generator_module,
            benchmark_name=f"Without Cache (n={sample_size})",
        )
        no_cache_stats = no_cache_result.compute_stats()
        
        # Print comparison
        print_quick_comparison(lru_stats, no_cache_stats, sample_size)
        
        all_results.append({
            "sample_size": sample_size,
            "with_lru": lru_stats,
            "without_cache": no_cache_stats,
        })
    
    # === 4. Summary ===
    print(f"\n{'='*70}")
    print("📈 SUMMARY ACROSS ALL SAMPLE SIZES")
    print(f"{'='*70}\n")
    
    print(f"{'Sample Size':<15} {'Avg Speedup':<15} {'Throughput Gain':<20}")
    print(f"{'-'*70}")
    
    for result in all_results:
        speedup = result['without_cache']['avg_latency'] / result['with_lru']['avg_latency']
        throughput_gain = ((result['with_lru']['throughput'] - result['without_cache']['throughput']) / 
                          result['without_cache']['throughput'] * 100)
        print(f"{result['sample_size']:<15} {speedup:<15.2f}x {throughput_gain:>18.1f}%")
    
    print(f"\n{'='*70}")
    print("✅ Quick benchmark completed!")
    print(f"{'='*70}\n")
    
    # Save results
    output_file = "quick_benchmark_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": all_results
        }, f, indent=2)
    print(f"💾 Results saved to {output_file}")


if __name__ == "__main__":
    main()


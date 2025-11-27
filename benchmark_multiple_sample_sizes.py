"""
Benchmark script that tests multiple sample sizes and saves results for visualization.
Tests three cache strategies across different sample sizes.
"""

import os
import json
import kuzu
import dspy
import time
from typing import Dict, List
from dotenv import load_dotenv
from text_2_cypher import (
    ExemplarSelector,
    QueryGenerator,
    CypherPostProcessor,
)
from cache_method import LRUDataManager, QueryNormalizer
from graph_rag_workflow import (
    setup_llm,
    get_schema_dict,
    PruneSchema,
    AnswerQuestion,
    Text2Cypher,
)
from benchmark_cache_strategies import (
    NoCacheManager,
    CacheStrategy,
    process_question_with_strategy,
    generate_test_questions,
)


def run_benchmark_for_sample_size(
    sample_size: int,
    base_questions: List[str],
    conn: kuzu.Connection,
    prune_module,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
) -> Dict:
    """Run benchmark for a specific sample size across all strategies."""
    print(f"\n{'='*100}")
    print(f"📊 BENCHMARKING SAMPLE SIZE: {sample_size}")
    print(f"{'='*100}")
    
    # Generate test questions for this sample size
    repeat_factor = max(1, sample_size // len(base_questions) + 1)
    test_questions = generate_test_questions(base_questions, repeat_factor)[:sample_size]
    
    # Define strategies
    strategies = [
        CacheStrategy("No Cache", NoCacheManager(), use_normalizer=False),
        CacheStrategy("LRU Cache (Basic)", LRUDataManager(cache_size=128), use_normalizer=False),
        CacheStrategy("LRU Cache + Normalizer", LRUDataManager(cache_size=128), use_normalizer=True),
    ]
    
    # Run benchmarks for each strategy
    results = {}
    
    for strategy in strategies:
        print(f"\n  🔄 Testing: {strategy.name}")
        
        # Reset strategy metrics
        strategy.query_metrics = []
        strategy.total_time = 0.0
        strategy.total_tokens = 0
        strategy.cache_hits = 0
        strategy.cache_misses = 0
        
        # Run queries
        for i, question in enumerate(test_questions, 1):
            latency, tokens, was_hit = process_question_with_strategy(
                question=question,
                conn=conn,
                prune_module=prune_module,
                strategy=strategy,
                exemplar_selector=exemplar_selector,
                query_generator=query_generator,
                post_processor=post_processor,
                answer_generator_module=answer_generator_module,
            )
            
            strategy.record_query(latency, tokens, was_hit)
            
            # Progress update every 10 queries
            if i % 10 == 0 or i == len(test_questions):
                hits = strategy.cache_hits
                hit_rate = (hits / i * 100) if i > 0 else 0
                print(f"     Progress: {i}/{len(test_questions)} | Hit Rate: {hit_rate:.1f}%")
        
        # Store results
        stats = strategy.get_stats()
        results[strategy.name] = stats
        
        print(f"     ✅ Completed | Hit Rate: {stats['cache_hit_rate']:.1f}% | "
              f"Throughput: {stats['throughput_tokens_per_sec_aggregate']:.1f} tokens/sec")
        
        # Small delay between strategies
        time.sleep(1)
    
    return {
        "sample_size": sample_size,
        "strategies": results
    }


def main():
    """Main benchmark execution across multiple sample sizes."""
    print("="*100)
    print("🚀 MULTI-SAMPLE SIZE CACHE STRATEGY BENCHMARK")
    print("="*100)
    print("Testing three strategies across multiple sample sizes:")
    print("  1. No Cache")
    print("  2. LRU Cache (Basic)")
    print("  3. LRU Cache + Query Normalizer")
    print("="*100)
    
    # === 1. Setup ===
    print("\n📦 Setting up components...")
    load_dotenv()
    
    lm = setup_llm()
    if not lm:
        print("❌ Failed to setup LLM")
        return
    
    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name, read_only=True)
    conn = kuzu.Connection(db)
    
    # Load exemplars
    try:
        with open('exemplars.json', 'r') as f:
            exemplars = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading exemplars.json: {e}")
        return
    
    exemplar_selector = ExemplarSelector(exemplars=exemplars)
    post_processor = CypherPostProcessor()
    
    text2cypher_predictor = dspy.ChainOfThought(Text2Cypher)
    query_generator = QueryGenerator(conn=conn, text2cypher_predictor=text2cypher_predictor)
    
    prune_module = dspy.ChainOfThought(PruneSchema)
    answer_generator_module = dspy.ChainOfThought(AnswerQuestion)
    
    print("✅ Setup completed!")
    
    # === 2. Define Test Questions ===
    base_questions = [
        "Who won the Nobel Prize in Physics?",
        "List all Nobel laureates in Chemistry",
        "How many prizes were awarded after 2000?",
        "Which scholars won multiple Nobel Prizes?",
        "Who was affiliated with University of Cambridge?",
        "List all female Nobel laureates",
        "Which country has the most Nobel Prize winners?",
        "Who won the Nobel Peace Prize in 1964?",
    ]
    
    # === 3. Define Sample Sizes to Test ===
    sample_sizes = [10, 20, 30, 50, 100]  # You can adjust these
    
    print(f"\n📋 Test Configuration:")
    print(f"   Base questions: {len(base_questions)}")
    print(f"   Sample sizes to test: {sample_sizes}")
    print(f"   Total benchmarks: {len(sample_sizes)} sample sizes × 3 strategies = {len(sample_sizes) * 3}")
    
    # === 4. Run Benchmarks for Each Sample Size ===
    all_results = []
    
    for sample_size in sample_sizes:
        result = run_benchmark_for_sample_size(
            sample_size=sample_size,
            base_questions=base_questions,
            conn=conn,
            prune_module=prune_module,
            exemplar_selector=exemplar_selector,
            query_generator=query_generator,
            post_processor=post_processor,
            answer_generator_module=answer_generator_module,
        )
        all_results.append(result)
        
        # Delay between sample sizes
        print(f"\n  ⏸️  Waiting 3 seconds before next sample size...")
        time.sleep(3)
    
    # === 5. Save Results ===
    output_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sample_sizes": sample_sizes,
        "base_questions_count": len(base_questions),
        "results": all_results
    }
    
    filename = "cache_strategies_multiple_sizes.json"
    with open(filename, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'='*100}")
    print(f"✅ Benchmark completed successfully!")
    print(f"💾 Results saved to {filename}")
    print(f"{'='*100}")
    
    # === 6. Print Summary ===
    print("\n📊 SUMMARY ACROSS SAMPLE SIZES:")
    print(f"{'Sample Size':<15} {'No Cache':<25} {'LRU Basic':<25} {'LRU + Norm':<25}")
    print(f"{'':<15} {'Hit%':<12} {'Tput':<12} {'Hit%':<12} {'Tput':<12} {'Hit%':<12} {'Tput':<12}")
    print("-" * 100)
    
    for result in all_results:
        size = result["sample_size"]
        no_cache = result["strategies"]["No Cache"]
        lru_basic = result["strategies"]["LRU Cache (Basic)"]
        lru_norm = result["strategies"]["LRU Cache + Normalizer"]
        
        print(f"{size:<15} "
              f"{no_cache['cache_hit_rate']:<12.1f} "
              f"{no_cache['throughput_tokens_per_sec_aggregate']:<12.1f} "
              f"{lru_basic['cache_hit_rate']:<12.1f} "
              f"{lru_basic['throughput_tokens_per_sec_aggregate']:<12.1f} "
              f"{lru_norm['cache_hit_rate']:<12.1f} "
              f"{lru_norm['throughput_tokens_per_sec_aggregate']:<12.1f}")


if __name__ == "__main__":
    main()


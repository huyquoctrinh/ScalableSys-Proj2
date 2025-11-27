"""
Comprehensive benchmark comparing three cache strategies:
1. No Cache
2. LRU Cache (basic)
3. LRU Cache with Query Normalizer

Measures both per-query and aggregate token throughput.
"""

import os
import json
import kuzu
import dspy
import time
import statistics
from typing import Dict, List, Tuple
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


def count_tokens(text: str) -> int:
    """
    Count tokens from text using tiktoken or fallback.
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except (ImportError, Exception):
        # Fallback: ~4 characters per token
        return len(text) // 4


class NoCacheManager:
    """Dummy cache manager that never caches anything."""
    def __init__(self):
        self.cache = type('obj', (object,), {'maxsize': 0})()
    
    def get_data(self, key):
        return None
    
    def set_data(self, key, value):
        pass
    
    def _hash(self, key):
        return key


class CacheStrategy:
    """Represents a cache strategy for benchmarking."""
    def __init__(self, name: str, cache_manager, use_normalizer: bool = False):
        self.name = name
        self.cache_manager = cache_manager
        self.use_normalizer = use_normalizer
        
        # Per-query metrics
        self.query_metrics = []  # List of {latency, tokens, was_hit}
        
        # Aggregate metrics
        self.total_time = 0.0
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_query(self, latency: float, tokens: int, was_hit: bool):
        """Record metrics for a single query."""
        self.query_metrics.append({
            "latency": latency,
            "tokens": tokens,
            "was_hit": was_hit,
            "tokens_per_sec": tokens / latency if latency > 0 else 0
        })
        self.total_time += latency
        self.total_tokens += tokens
        
        if was_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_stats(self) -> Dict:
        """Compute comprehensive statistics."""
        if not self.query_metrics:
            return {}
        
        latencies = [m["latency"] for m in self.query_metrics]
        tokens_per_query = [m["tokens"] for m in self.query_metrics]
        tokens_per_sec_per_query = [m["tokens_per_sec"] for m in self.query_metrics]
        
        total_queries = len(self.query_metrics)
        
        return {
            "name": self.name,
            "total_queries": total_queries,
            "total_time": self.total_time,
            "total_tokens": self.total_tokens,
            
            # Latency metrics
            "avg_latency": statistics.mean(latencies),
            "median_latency": statistics.median(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "stdev_latency": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            
            # Token metrics per query
            "avg_tokens_per_query": statistics.mean(tokens_per_query),
            "total_tokens_generated": self.total_tokens,
            
            # Throughput metrics
            "throughput_queries_per_sec": total_queries / self.total_time if self.total_time > 0 else 0,
            "throughput_tokens_per_sec_aggregate": self.total_tokens / self.total_time if self.total_time > 0 else 0,
            "avg_tokens_per_sec_per_query": statistics.mean(tokens_per_sec_per_query),
            "median_tokens_per_sec_per_query": statistics.median(tokens_per_sec_per_query),
            
            # Cache metrics
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (self.cache_hits / total_queries * 100) if total_queries > 0 else 0,
        }


def process_question_with_strategy(
    question: str,
    conn: kuzu.Connection,
    prune_module,
    strategy: CacheStrategy,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
) -> Tuple[float, int, bool]:
    """
    Process a single question with given cache strategy.
    
    Returns:
        (elapsed_time, tokens_generated, was_cache_hit)
    """
    start_time = time.time()
    was_cache_hit = False
    tokens_generated = 0
    
    # Normalize question if strategy uses normalizer
    if strategy.use_normalizer:
        normalized_question = QueryNormalizer.normalize(question)
    else:
        normalized_question = question
    
    # === 1. Prune Schema and Generate Cache Key ===
    input_schema = get_schema_dict(conn)
    pruned_schema_result = prune_module(
        question=normalized_question, 
        input_schema=json.dumps(input_schema, indent=2)
    )
    pruned_schema = pruned_schema_result.pruned_schema.model_dump()
    schema_str = json.dumps(pruned_schema, sort_keys=True)
    cache_key = f"{normalized_question}|{schema_str}"
    hashed_key = strategy.cache_manager._hash(cache_key)

    # === 2. Check Cache for Context ===
    cached_data = strategy.cache_manager.get_data(hashed_key)

    if cached_data:
        # Cache hit - use cached context to generate answer
        was_cache_hit = True
        final_query = cached_data["query"]
        context = cached_data["context"]
        
        # Generate answer from cached context
        if context is not None:
            answer_obj = answer_generator_module(
                question=question, cypher_query=final_query, context=str(context)
            )
            final_answer = answer_obj.response
            tokens_generated = count_tokens(final_answer)
        
        elapsed_time = time.time() - start_time
        return elapsed_time, tokens_generated, was_cache_hit

    # === 3. Cache Miss: Run Full Pipeline ===
    # Generate and Process Query
    top_k_exemplars = exemplar_selector.select_top_k(question, k=2)
    generated_query, _ = query_generator.generate_with_refinement(
        question=question, 
        schema=json.dumps(pruned_schema, indent=2), 
        examples=str(top_k_exemplars)
    )
    final_query = post_processor.process(generated_query)

    # Execute Query
    try:
        result = conn.execute(final_query)
        df = result.get_as_df()
        context = [item for row in df.values for item in row]
    except RuntimeError as e:
        context = None

    # Cache the context
    if context is not None:
        strategy.cache_manager.set_data(hashed_key, {"query": final_query, "context": context})
        
        # Generate final answer
        answer_obj = answer_generator_module(
            question=question, cypher_query=final_query, context=str(context)
        )
        final_answer = answer_obj.response
        tokens_generated = count_tokens(final_answer)
    
    elapsed_time = time.time() - start_time
    return elapsed_time, tokens_generated, was_cache_hit


def run_benchmark_strategy(
    strategy: CacheStrategy,
    questions: List[str],
    conn: kuzu.Connection,
    prune_module,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
) -> CacheStrategy:
    """Run benchmark for a single cache strategy."""
    print(f"\n{'='*80}")
    print(f"🔄 Running benchmark: {strategy.name}")
    print(f"   Processing {len(questions)} queries...")
    print(f"   Normalizer: {'ENABLED' if strategy.use_normalizer else 'DISABLED'}")
    print(f"{'='*80}")
    
    for i, question in enumerate(questions, 1):
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
        
        # Progress update
        if i % 5 == 0 or i == len(questions):
            hits = strategy.cache_hits
            hit_rate = (hits / i * 100) if i > 0 else 0
            tokens_so_far = strategy.total_tokens
            avg_tokens_per_sec = strategy.total_tokens / strategy.total_time if strategy.total_time > 0 else 0
            
            print(f"   Progress: {i}/{len(questions)} | "
                  f"Hits: {hits} ({hit_rate:.1f}%) | "
                  f"Tokens: {tokens_so_far} | "
                  f"Avg tokens/sec: {avg_tokens_per_sec:.1f}")
    
    stats = strategy.get_stats()
    print(f"\n   ✅ Completed {len(questions)} queries")
    print(f"   📊 Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    print(f"   📝 Total tokens: {stats['total_tokens_generated']}")
    print(f"   ⚡ Aggregate throughput: {stats['throughput_tokens_per_sec_aggregate']:.1f} tokens/sec")
    print(f"   📈 Avg per-query throughput: {stats['avg_tokens_per_sec_per_query']:.1f} tokens/sec")
    
    return strategy


def print_comparison_report(strategies: List[CacheStrategy]):
    """Print comprehensive comparison of all strategies."""
    print("\n" + "="*100)
    print("📊 COMPREHENSIVE CACHE STRATEGY COMPARISON")
    print("="*100)
    
    stats_list = [s.get_stats() for s in strategies]
    
    # Find baseline (no cache)
    baseline = next((s for s in stats_list if "No Cache" in s["name"]), stats_list[0])
    
    print(f"\n{'='*100}")
    print("LATENCY METRICS")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Avg (s)':<12} {'Median (s)':<12} {'Min (s)':<12} {'Max (s)':<12} {'StdDev (s)':<12}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        print(f"{stats['name']:<30} "
              f"{stats['avg_latency']:<12.3f} "
              f"{stats['median_latency']:<12.3f} "
              f"{stats['min_latency']:<12.3f} "
              f"{stats['max_latency']:<12.3f} "
              f"{stats['stdev_latency']:<12.3f}")
    
    # Add latency comparison section
    print(f"\n{'='*100}")
    print("LATENCY COMPARISON & IMPROVEMENTS")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'vs Baseline':<20} {'Latency Reduction':<20} {'Speedup':<15}")
    print(f"{'':>30} {'(seconds)':<20} {'(%)':<20} {'(x)':<15}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        if stats['name'] == baseline['name']:
            print(f"{stats['name']:<30} {'baseline':<20} {'baseline':<20} {'1.00x':<15}")
        else:
            latency_diff = baseline['avg_latency'] - stats['avg_latency']
            latency_reduction = (latency_diff / baseline['avg_latency'] * 100) if baseline['avg_latency'] > 0 else 0
            speedup = baseline['avg_latency'] / stats['avg_latency'] if stats['avg_latency'] > 0 else 0
            
            print(f"{stats['name']:<30} "
                  f"{latency_diff:>18.3f}s "
                  f"{latency_reduction:>18.1f}% "
                  f"{speedup:>13.2f}x")
    
    print(f"\n{'='*100}")
    print("TOKEN THROUGHPUT METRICS")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Aggregate':<15} {'Avg Per-Query':<15} {'Median Per-Query':<15}")
    print(f"{'':>30} {'(tokens/sec)':<15} {'(tokens/sec)':<15} {'(tokens/sec)':<15}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        print(f"{stats['name']:<30} "
              f"{stats['throughput_tokens_per_sec_aggregate']:<15.1f} "
              f"{stats['avg_tokens_per_sec_per_query']:<15.1f} "
              f"{stats['median_tokens_per_sec_per_query']:<15.1f}")
    
    print(f"\n{'='*100}")
    print("QUERY THROUGHPUT & TOKENS")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Queries/sec':<15} {'Total Tokens':<15} {'Avg Tokens/Query':<15}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        print(f"{stats['name']:<30} "
              f"{stats['throughput_queries_per_sec']:<15.3f} "
              f"{stats['total_tokens_generated']:<15} "
              f"{stats['avg_tokens_per_query']:<15.1f}")
    
    print(f"\n{'='*100}")
    print("CACHE PERFORMANCE")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Hit Rate':<15} {'Hits':<10} {'Misses':<10} {'Total':<10}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        print(f"{stats['name']:<30} "
              f"{stats['cache_hit_rate']:<15.1f}% "
              f"{stats['cache_hits']:<10} "
              f"{stats['cache_misses']:<10} "
              f"{stats['total_queries']:<10}")
    
    print(f"\n{'='*100}")
    print("PERFORMANCE IMPROVEMENT vs NO CACHE")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Latency':<15} {'Token Throughput':<20} {'Time Saved':<15}")
    print(f"{'':>30} {'Improvement':<15} {'(Aggregate)':<20} {'(seconds)':<15}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        if stats['name'] == baseline['name']:
            print(f"{stats['name']:<30} {'baseline':<15} {'baseline':<20} {'baseline':<15}")
        else:
            lat_improvement = (baseline['avg_latency'] - stats['avg_latency']) / baseline['avg_latency'] * 100
            throughput_improvement = ((stats['throughput_tokens_per_sec_aggregate'] - 
                                      baseline['throughput_tokens_per_sec_aggregate']) / 
                                     baseline['throughput_tokens_per_sec_aggregate'] * 100)
            time_saved = baseline['total_time'] - stats['total_time']
            
            print(f"{stats['name']:<30} "
                  f"{lat_improvement:>13.1f}% "
                  f"{throughput_improvement:>18.1f}% "
                  f"{time_saved:>13.1f}s")
    
    print(f"\n{'='*100}")
    print("SPEEDUP FACTORS vs NO CACHE")
    print(f"{'='*100}")
    print(f"{'Strategy':<30} {'Latency Speedup':<20} {'Throughput Speedup':<20}")
    print(f"{'-'*100}")
    
    for stats in stats_list:
        if stats['name'] == baseline['name']:
            print(f"{stats['name']:<30} {'1.00x':<20} {'1.00x':<20}")
        else:
            latency_speedup = baseline['avg_latency'] / stats['avg_latency']
            throughput_speedup = (stats['throughput_tokens_per_sec_aggregate'] / 
                                 baseline['throughput_tokens_per_sec_aggregate'])
            
            print(f"{stats['name']:<30} "
                  f"{latency_speedup:<20.2f}x "
                  f"{throughput_speedup:<20.2f}x")


def save_results(strategies: List[CacheStrategy], filename: str = "cache_strategies_results.json"):
    """Save benchmark results to JSON file."""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "strategies": [
            {
                "name": s.name,
                "stats": s.get_stats(),
                "per_query_metrics": s.query_metrics[:10]  # Save first 10 for inspection
            }
            for s in strategies
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {filename}")


def generate_test_questions(base_questions: List[str], repeat_factor: int = 3) -> List[str]:
    """
    Generate test questions with variations to test cache effectiveness.
    
    Includes:
    - Original questions
    - Case variations
    - Punctuation variations
    - Whitespace variations
    """
    import random
    
    all_questions = []
    
    for _ in range(repeat_factor):
        for q in base_questions:
            # Original
            all_questions.append(q)
            
            # Case variation
            all_questions.append(q.upper() if random.random() > 0.5 else q.lower())
            
            # Punctuation variation
            variations = [
                q,
                q.rstrip('?') + '?',
                q.rstrip('?.') + '.',
                q + '?'
            ]
            all_questions.append(random.choice(variations))
    
    # Shuffle to simulate realistic query patterns
    random.shuffle(all_questions)
    
    return all_questions


def main():
    """Main benchmark execution."""
    print("="*100)
    print("🚀 COMPREHENSIVE CACHE STRATEGY BENCHMARK")
    print("="*100)
    print("Comparing three strategies:")
    print("  1. No Cache - Full pipeline every time")
    print("  2. LRU Cache - Basic caching")
    print("  3. LRU Cache + Query Normalizer - Optimized caching")
    print("="*100)
    
    # === 1. Setup ===
    print("\n📦 Setting up components...")
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
    
    # Generate test set with variations
    sample_size = 30  # Total queries to test
    repeat_factor = sample_size // len(base_questions) + 1
    test_questions = generate_test_questions(base_questions, repeat_factor)[:sample_size]
    
    print(f"\n📋 Test Configuration:")
    print(f"   Base questions: {len(base_questions)}")
    print(f"   Total test queries: {len(test_questions)}")
    print(f"   (includes variations to test cache & normalizer effectiveness)")
    
    # === 3. Define Strategies ===
    strategies = [
        CacheStrategy("1. No Cache", NoCacheManager(), use_normalizer=False),
        CacheStrategy("2. LRU Cache (Basic)", LRUDataManager(cache_size=128), use_normalizer=False),
        CacheStrategy("3. LRU Cache + Normalizer", LRUDataManager(cache_size=128), use_normalizer=True),
    ]
    
    # === 4. Run Benchmarks ===
    results = []
    
    for strategy in strategies:
        result = run_benchmark_strategy(
            strategy=strategy,
            questions=test_questions,
            conn=conn,
            prune_module=prune_module,
            exemplar_selector=exemplar_selector,
            query_generator=query_generator,
            post_processor=post_processor,
            answer_generator_module=answer_generator_module,
        )
        results.append(result)
        
        # Small delay between benchmarks
        time.sleep(2)
    
    # === 5. Print Comparison ===
    print_comparison_report(results)
    
    # === 6. Save Results ===
    save_results(results)
    
    print("\n" + "="*100)
    print("✅ Benchmark completed successfully!")
    print("="*100)
    
    # Print key insights
    print("\n💡 KEY INSIGHTS:")
    stats_list = [s.get_stats() for s in results]
    
    lru_basic = stats_list[1]
    lru_normalized = stats_list[2]
    no_cache = stats_list[0]
    
    basic_improvement = (lru_basic['cache_hit_rate'] - no_cache['cache_hit_rate'])
    normalizer_improvement = (lru_normalized['cache_hit_rate'] - lru_basic['cache_hit_rate'])
    
    print(f"   • LRU Cache improves hit rate by: {basic_improvement:.1f}%")
    print(f"   • Query Normalizer adds: +{normalizer_improvement:.1f}% hit rate")
    print(f"   • Overall improvement: {lru_normalized['cache_hit_rate']:.1f}% hit rate")
    print(f"   • Token throughput boost: {lru_normalized['throughput_tokens_per_sec_aggregate'] / no_cache['throughput_tokens_per_sec_aggregate']:.2f}x")
    print(f"   • Time saved: {no_cache['total_time'] - lru_normalized['total_time']:.1f}s")
    print(f"   • Latency reduction: {((no_cache['avg_latency'] - lru_normalized['avg_latency']) / no_cache['avg_latency'] * 100):.1f}%")
    print(f"   • Latency speedup: {no_cache['avg_latency'] / lru_normalized['avg_latency']:.2f}x")


if __name__ == "__main__":
    main()


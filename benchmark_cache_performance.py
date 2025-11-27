"""
Benchmark script to compare latency and throughput of Graph RAG system
with and without LRU cache for different sample sizes.

Throughput is measured in both:
- Queries per second
- Tokens inferred per second (more accurate LLM performance metric)
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
from cache_method import LRUDataManager
from graph_rag_workflow import (
    setup_llm,
    get_schema_dict,
    PruneSchema,
    AnswerQuestion,
    Text2Cypher,
)


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


class BenchmarkResult:
    """Store benchmark results for a single test run."""
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.total_time: float = 0.0
        self.sample_size: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.total_tokens: int = 0
        self.tokens_per_query: List[int] = []
    
    def add_query(self, latency: float, was_cache_hit: bool = False, tokens: int = 0):
        """Add a query latency measurement with token count."""
        self.latencies.append(latency)
        self.tokens_per_query.append(tokens)
        self.total_tokens += tokens
        if was_cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def compute_stats(self) -> Dict:
        """Compute statistics from collected latencies and tokens."""
        if not self.latencies:
            return {}
        
        self.sample_size = len(self.latencies)
        self.total_time = sum(self.latencies)
        
        return {
            "name": self.name,
            "sample_size": self.sample_size,
            "total_time": self.total_time,
            "avg_latency": statistics.mean(self.latencies),
            "median_latency": statistics.median(self.latencies),
            "min_latency": min(self.latencies),
            "max_latency": max(self.latencies),
            "stdev_latency": statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0,
            "throughput_queries": self.sample_size / self.total_time if self.total_time > 0 else 0,
            "throughput_tokens": self.total_tokens / self.total_time if self.total_time > 0 else 0,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_query": statistics.mean(self.tokens_per_query) if self.tokens_per_query else 0,
            "p95_latency": statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) >= 20 else max(self.latencies),
            "p99_latency": statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) >= 100 else max(self.latencies),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (self.cache_hits / self.sample_size * 100) if self.sample_size > 0 else 0,
        }


def count_tokens(text: str) -> int:
    """
    Count tokens from text.
    First tries to use tiktoken (OpenAI tokenizer) if available.
    Falls back to simple heuristic: ~4 characters per token (GPT tokenizer average).
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4/3.5-turbo encoding
        return len(encoding.encode(text))
    except (ImportError, Exception):
        # Fallback to simple heuristic
        return len(text) // 4

def process_question_benchmark(
    question: str,
    conn: kuzu.Connection,
    prune_module,
    cache_manager,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
    is_cache_enabled: bool = True,
) -> Tuple[float, bool, int]:
    """
    Process a single question and return the latency, cache hit status, and tokens generated.
    
    Returns:
        (elapsed_time, was_cache_hit, tokens_generated)
    """
    start_time = time.time()
    was_cache_hit = False
    tokens_generated = 0
    
    # === 1. Prune Schema and Generate Cache Key ===
    input_schema = get_schema_dict(conn)
    pruned_schema_result = prune_module(question=question, input_schema=json.dumps(input_schema, indent=2))
    pruned_schema = pruned_schema_result.pruned_schema.model_dump()
    schema_str = json.dumps(pruned_schema, sort_keys=True)
    cache_key = f"{question}|{schema_str}"
    hashed_key = cache_manager._hash(cache_key)

    # === 2. Check Cache for Context (only if cache enabled) ===
    cached_data = cache_manager.get_data(hashed_key) if is_cache_enabled else None

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
        return elapsed_time, was_cache_hit, tokens_generated

    # === 3. Cache Miss: Run Full Pipeline ===
    # Generate and Process Query
    top_k_exemplars = exemplar_selector.select_top_k(question, k=2)
    generated_query, _ = query_generator.generate_with_refinement(
        question=question, schema=json.dumps(pruned_schema, indent=2), examples=str(top_k_exemplars)
    )
    final_query = post_processor.process(generated_query)

    # Execute Query
    try:
        result = conn.execute(final_query)
        df = result.get_as_df()
        context = [item for row in df.values for item in row]
    except RuntimeError as e:
        context = None

    # Cache the context (not the final answer) - only if cache enabled
    if context is not None and is_cache_enabled:
        cache_manager.set_data(hashed_key, {"query": final_query, "context": context})
        
        # Generate final answer
        answer_obj = answer_generator_module(
            question=question, cypher_query=final_query, context=str(context)
        )
        final_answer = answer_obj.response
        tokens_generated = count_tokens(final_answer)
    elif context is not None:
        # No cache - just generate answer
        answer_obj = answer_generator_module(
            question=question, cypher_query=final_query, context=str(context)
        )
        final_answer = answer_obj.response
        tokens_generated = count_tokens(final_answer)
    
    elapsed_time = time.time() - start_time
    return elapsed_time, was_cache_hit, tokens_generated


def generate_test_questions(base_questions: List[str], repeat_factor: int = 2) -> List[str]:
    """
    Generate a list of test questions with repetitions to test cache effectiveness.
    
    Args:
        base_questions: Base set of unique questions
        repeat_factor: How many times to repeat the questions (simulates real workload)
    
    Returns:
        List of questions with repetitions mixed in
    """
    import random
    
    # Create a list with original questions repeated
    all_questions = base_questions * repeat_factor
    
    # Shuffle to simulate realistic query patterns
    random.shuffle(all_questions)
    
    return all_questions


def run_benchmark(
    questions: List[str],
    conn: kuzu.Connection,
    prune_module,
    cache_manager,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
    benchmark_name: str,
    is_cache_enabled: bool = True,
) -> BenchmarkResult:
    """Run benchmark for a set of questions with given cache manager."""
    print(f"\n🔄 Running benchmark: {benchmark_name}")
    print(f"   Processing {len(questions)} queries...")
    print(f"   Cache {'ENABLED' if is_cache_enabled else 'DISABLED'}")
    
    result = BenchmarkResult(benchmark_name)
    
    for i, question in enumerate(questions, 1):
        latency, was_cache_hit, tokens = process_question_benchmark(
            question=question,
            conn=conn,
            prune_module=prune_module,
            cache_manager=cache_manager,
            exemplar_selector=exemplar_selector,
            query_generator=query_generator,
            post_processor=post_processor,
            answer_generator_module=answer_generator_module,
            is_cache_enabled=is_cache_enabled,
        )
        result.add_query(latency, was_cache_hit, tokens)
        
        if i % 10 == 0:
            hits = result.cache_hits
            hit_rate = (hits / i * 100) if i > 0 else 0
            tokens_so_far = result.total_tokens
            print(f"   Progress: {i}/{len(questions)} queries | Cache hits: {hits} ({hit_rate:.1f}%) | Tokens: {tokens_so_far}")
    
    print(f"   ✅ Completed {len(questions)} queries")
    print(f"   📊 Final cache hit rate: {result.cache_hits}/{len(questions)} ({result.cache_hits/len(questions)*100:.1f}%)")
    print(f"   📝 Total tokens generated: {result.total_tokens}")
    return result


def print_comparison_report(results: List[Tuple[BenchmarkResult, Dict]]):
    """Print a detailed comparison report of all benchmark results."""
    print("\n" + "="*80)
    print("📊 BENCHMARK COMPARISON REPORT: LRU Cache vs No Cache")
    print("="*80)
    
    # Group results by sample size
    sample_sizes = sorted(set(stats['sample_size'] for _, stats in results))
    
    for sample_size in sample_sizes:
        print(f"\n{'='*80}")
        print(f"Sample Size: {sample_size} queries")
        print(f"{'='*80}")
        
        # Get results for this sample size
        size_results = [(r, s) for r, s in results if s['sample_size'] == sample_size]
        
        if len(size_results) < 2:
            continue
        
        # Assume first is with LRU, second is without
        lru_result, lru_stats = size_results[0]
        no_cache_result, no_cache_stats = size_results[1]
        
        print(f"\n📈 LATENCY METRICS")
        print(f"{'-'*80}")
        print(f"{'Metric':<25} {'With LRU Cache':<20} {'Without Cache':<20} {'Improvement':<15}")
        print(f"{'-'*80}")
        
        # Average Latency
        avg_improvement = ((no_cache_stats['avg_latency'] - lru_stats['avg_latency']) / 
                          no_cache_stats['avg_latency'] * 100)
        print(f"{'Average Latency':<25} {lru_stats['avg_latency']:<20.3f} "
              f"{no_cache_stats['avg_latency']:<20.3f} {avg_improvement:>13.1f}%")
        
        # Median Latency
        med_improvement = ((no_cache_stats['median_latency'] - lru_stats['median_latency']) / 
                          no_cache_stats['median_latency'] * 100)
        print(f"{'Median Latency':<25} {lru_stats['median_latency']:<20.3f} "
              f"{no_cache_stats['median_latency']:<20.3f} {med_improvement:>13.1f}%")
        
        # P95 Latency
        p95_improvement = ((no_cache_stats['p95_latency'] - lru_stats['p95_latency']) / 
                          no_cache_stats['p95_latency'] * 100)
        print(f"{'P95 Latency':<25} {lru_stats['p95_latency']:<20.3f} "
              f"{no_cache_stats['p95_latency']:<20.3f} {p95_improvement:>13.1f}%")
        
        # Min/Max Latency
        print(f"{'Min Latency':<25} {lru_stats['min_latency']:<20.3f} "
              f"{no_cache_stats['min_latency']:<20.3f} {'-':<15}")
        print(f"{'Max Latency':<25} {lru_stats['max_latency']:<20.3f} "
              f"{no_cache_stats['max_latency']:<20.3f} {'-':<15}")
        
        # Standard Deviation
        print(f"{'Std Dev Latency':<25} {lru_stats['stdev_latency']:<20.3f} "
              f"{no_cache_stats['stdev_latency']:<20.3f} {'-':<15}")
        
        print(f"\n⚡ THROUGHPUT METRICS")
        print(f"{'-'*80}")
        print(f"{'Metric':<25} {'With LRU Cache':<20} {'Without Cache':<20} {'Improvement':<15}")
        print(f"{'-'*80}")
        
        # Query Throughput
        throughput_improvement = ((lru_stats['throughput_queries'] - no_cache_stats['throughput_queries']) / 
                                 no_cache_stats['throughput_queries'] * 100)
        print(f"{'Throughput (queries/sec)':<25} {lru_stats['throughput_queries']:<20.3f} "
              f"{no_cache_stats['throughput_queries']:<20.3f} {throughput_improvement:>13.1f}%")
        
        # Token Throughput
        token_throughput_improvement = ((lru_stats['throughput_tokens'] - no_cache_stats['throughput_tokens']) / 
                                       no_cache_stats['throughput_tokens'] * 100)
        print(f"{'Throughput (tokens/sec)':<25} {lru_stats['throughput_tokens']:<20.1f} "
              f"{no_cache_stats['throughput_tokens']:<20.1f} {token_throughput_improvement:>13.1f}%")
        
        # Total Tokens
        print(f"{'Total Tokens Generated':<25} {lru_stats['total_tokens']:<20} "
              f"{no_cache_stats['total_tokens']:<20} {'-':<15}")
        print(f"{'Avg Tokens per Query':<25} {lru_stats['avg_tokens_per_query']:<20.1f} "
              f"{no_cache_stats['avg_tokens_per_query']:<20.1f} {'-':<15}")
        
        # Total Time
        time_saved = no_cache_stats['total_time'] - lru_stats['total_time']
        time_improvement = (time_saved / no_cache_stats['total_time'] * 100)
        print(f"{'Total Time (seconds)':<25} {lru_stats['total_time']:<20.3f} "
              f"{no_cache_stats['total_time']:<20.3f} {time_improvement:>13.1f}%")
        print(f"{'Time Saved (seconds)':<25} {time_saved:<20.3f}")
        
        print(f"\n🎯 SPEEDUP FACTOR")
        print(f"{'-'*80}")
        speedup = no_cache_stats['avg_latency'] / lru_stats['avg_latency']
        print(f"Average query with LRU cache is {speedup:.2f}x faster")
        
        print(f"\n📊 CACHE STATISTICS")
        print(f"{'-'*80}")
        print(f"{'Metric':<25} {'With LRU Cache':<20} {'Without Cache':<20}")
        print(f"{'-'*80}")
        print(f"{'Cache Hits':<25} {lru_stats['cache_hits']:<20} {no_cache_stats['cache_hits']:<20}")
        print(f"{'Cache Misses':<25} {lru_stats['cache_misses']:<20} {no_cache_stats['cache_misses']:<20}")
        print(f"{'Cache Hit Rate':<25} {lru_stats['cache_hit_rate']:<20.1f}% {no_cache_stats['cache_hit_rate']:<20.1f}%")
        
        # Cost estimation (assuming $0.002 per query for LLM calls)
        # With cache: only cache misses pay full cost, hits pay partial cost for answer gen
        lru_cost = (lru_stats['cache_misses'] * 0.002) + (lru_stats['cache_hits'] * 0.0002)
        no_cache_cost = no_cache_stats['cache_misses'] * 0.002
        cost_saved = no_cache_cost - lru_cost
        
        print(f"\n💰 ESTIMATED COST SAVINGS")
        print(f"{'-'*80}")
        print(f"Total cost (with cache): ${lru_cost:.4f}")
        print(f"Total cost (no cache): ${no_cache_cost:.4f}")
        print(f"Cost saved: ${cost_saved:.4f} ({cost_saved/no_cache_cost*100:.1f}%)")
        print(f"Cost per query (with cache): ${lru_cost / sample_size:.6f}")
        print(f"Cost per query (no cache): ${no_cache_cost / sample_size:.6f}")


def save_results_to_json(results: List[Tuple[BenchmarkResult, Dict]], filename: str = "benchmark_results.json"):
    """Save benchmark results to JSON file."""
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": [stats for _, stats in results]
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to {filename}")


def main():
    """Main benchmark execution."""
    print("="*80)
    print("🚀 Graph RAG Cache Performance Benchmark")
    print("="*80)
    print("This benchmark compares system performance with and without LRU cache")
    print("for different sample sizes.\n")
    
    # === 1. Setup ===
    print("📦 Setting up components...")
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
    
    # === 3. Define Sample Sizes ===
    sample_sizes = [20, 40, 60, 80]
    
    print(f"\n📋 Test Configuration:")
    print(f"   Base questions: {len(base_questions)}")
    print(f"   Sample sizes to test: {sample_sizes}")
    print(f"   Cache size: 128 entries")
    
    all_results = []
    
    # === 4. Run Benchmarks for Each Sample Size ===
    for sample_size in sample_sizes:
        print(f"\n{'='*80}")
        print(f"Testing with sample size: {sample_size} queries")
        print(f"{'='*80}")
        
        # Generate test questions with repetitions
        repeat_factor = (sample_size // len(base_questions)) + 1
        test_questions = generate_test_questions(base_questions, repeat_factor)[:sample_size]
        
        print(f"Generated {len(test_questions)} test queries (with repetitions for cache testing)")
        
        # Test WITH LRU Cache
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
            benchmark_name=f"With LRU Cache (n={sample_size})",
            is_cache_enabled=True,
        )
        lru_stats = lru_result.compute_stats()
        all_results.append((lru_result, lru_stats))
        
        # Small delay between tests
        time.sleep(2)
        
        # Test WITHOUT Cache
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
            is_cache_enabled=False,  # Disable caching for no-cache benchmark
        )
        no_cache_stats = no_cache_result.compute_stats()
        all_results.append((no_cache_result, no_cache_stats))
    
    # === 5. Print Comparison Report ===
    print_comparison_report(all_results)
    
    # === 6. Save Results ===
    save_results_to_json(all_results)
    
    print("\n" + "="*80)
    print("✅ Benchmark completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()


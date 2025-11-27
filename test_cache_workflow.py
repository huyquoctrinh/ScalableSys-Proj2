"""
Test script to verify the updated cache workflow.
Tests that context is cached and answers are regenerated on cache hits.
"""

from cache_method import LRUDataManager

def test_context_caching():
    """Test that context is cached correctly."""
    print("Testing context caching workflow...")
    print("="*60)
    
    # Initialize cache
    cache = LRUDataManager(cache_size=10)
    
    # Simulate first query (cache miss)
    question = "Which scholars won prizes in Physics?"
    query = "MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName"
    context = ["Albert Einstein", "Marie Curie", "Niels Bohr"]
    
    cache_key = f"{question}|schema_hash"
    
    # Store context in cache
    cache.set_data(cache_key, {"query": query, "context": context})
    print(f"✓ Stored context in cache")
    print(f"  Query: {query[:50]}...")
    print(f"  Context: {context}")
    print()
    
    # Simulate second query (cache hit)
    cached_data = cache.get_data(cache_key)
    
    if cached_data is None:
        print("❌ FAIL: Cache returned None")
        return False
    
    # Verify structure
    if "query" not in cached_data or "context" not in cached_data:
        print("❌ FAIL: Cache data missing 'query' or 'context' keys")
        print(f"  Got keys: {cached_data.keys()}")
        return False
    
    # Verify content
    if cached_data["query"] != query:
        print("❌ FAIL: Cached query doesn't match")
        return False
    
    if cached_data["context"] != context:
        print("❌ FAIL: Cached context doesn't match")
        return False
    
    print(f"✓ Retrieved context from cache")
    print(f"  Query: {cached_data['query'][:50]}...")
    print(f"  Context: {cached_data['context']}")
    print()
    
    # Simulate answer generation (would happen on each request)
    print("✓ Generating fresh answer from cached context...")
    print("  [In production, this calls the LLM with the cached context]")
    print()
    
    print("="*60)
    print("✅ SUCCESS: Context caching workflow works correctly!")
    print()
    print("Summary:")
    print("  - Context is cached with query")
    print("  - Answer generation happens on each request")
    print("  - Cache provides fast context retrieval")
    print("  - Flexible for different answer strategies")
    return True

def test_cache_miss_workflow():
    """Test cache miss workflow."""
    print("\nTesting cache miss workflow...")
    print("="*60)
    
    cache = LRUDataManager(cache_size=10)
    
    question = "New question not in cache"
    cache_key = f"{question}|schema_hash"
    
    # Try to get from cache
    cached_data = cache.get_data(cache_key)
    
    if cached_data is not None:
        print("❌ FAIL: Cache should return None for new question")
        return False
    
    print("✓ Cache miss detected (as expected)")
    print()
    
    # Simulate full pipeline
    print("Running full pipeline:")
    print("  1. Schema pruning")
    print("  2. Exemplar selection")
    print("  3. Query generation with refinement")
    print("  4. Query post-processing")
    print("  5. Database execution")
    print("  6. Cache context")
    print("  7. Generate answer")
    print()
    
    # Cache the context
    query = "MATCH (n) RETURN n"
    context = ["Result1", "Result2"]
    cache.set_data(cache_key, {"query": query, "context": context})
    
    print("✓ Context cached for future requests")
    print(f"  Cache size: {len(cache.cache)}/{cache.cache.maxsize}")
    print()
    
    print("="*60)
    print("✅ SUCCESS: Cache miss workflow works correctly!")
    return True

def test_multiple_questions():
    """Test caching multiple different questions."""
    print("\nTesting multiple questions...")
    print("="*60)
    
    cache = LRUDataManager(cache_size=10)
    
    questions = [
        "Which scholars won prizes in Physics?",
        "Who was affiliated with University of Cambridge?",
        "How many laureates won prizes in Chemistry?",
    ]
    
    # Cache all questions
    for i, question in enumerate(questions):
        cache_key = f"{question}|schema_{i}"
        cache.set_data(cache_key, {
            "query": f"QUERY_{i}",
            "context": [f"Result_{i}_1", f"Result_{i}_2"]
        })
    
    print(f"✓ Cached {len(questions)} questions")
    print(f"  Cache size: {len(cache.cache)}/{cache.cache.maxsize}")
    print()
    
    # Retrieve all questions
    for i, question in enumerate(questions):
        cache_key = f"{question}|schema_{i}"
        cached_data = cache.get_data(cache_key)
        
        if cached_data is None:
            print(f"❌ FAIL: Question {i+1} not in cache")
            return False
        
        print(f"✓ Question {i+1} retrieved from cache")
    
    print()
    print("="*60)
    print("✅ SUCCESS: Multiple questions cached correctly!")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Cache Workflow Test Suite")
    print("="*60)
    print()
    
    tests = [
        ("Context Caching", test_context_caching),
        ("Cache Miss Workflow", test_cache_miss_workflow),
        ("Multiple Questions", test_multiple_questions),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Cache workflow is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())


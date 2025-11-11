"""
Compare TF-IDF vs Neural embeddings for exemplar selection.

Run this to see which approach works better for your use case.
"""

import json
import time
from text_2_cypher.exemplar_selector import ExemplarSelector as TFIDFSelector

# Load exemplars
with open('exemplars.json', 'r') as f:
    exemplars = json.load(f)

# Test questions (different phrasings of similar concepts)
test_questions = [
    "Which scholars won prizes in Physics?",
    "Who received Nobel awards in Physics?",
    "List Physics Nobel laureates",
    "Show me Chemistry prize winners",
    "How many people got the Economics prize?",
]

print("=" * 70)
print("EMBEDDING COMPARISON TEST")
print("=" * 70)
print(f"\nLoaded {len(exemplars)} exemplars")
print(f"Testing with {len(test_questions)} questions\n")

# Initialize TF-IDF selector
print("Initializing TF-IDF selector...")
tfidf_selector = TFIDFSelector(exemplars)
print("✓ TF-IDF ready\n")

# Try to import neural selector (optional)
try:
    from text_2_cypher.exemplar_selector_neural import ExemplarSelector as NeuralSelector
    print("Initializing Neural selector...")
    neural_selector = NeuralSelector(exemplars)
    print("✓ Neural ready\n")
    use_neural = True
except ImportError as e:
    print(f"⚠️  Neural selector not available: {e}")
    print("   Using TF-IDF only\n")
    use_neural = False

# Test each question
for i, question in enumerate(test_questions, 1):
    print("=" * 70)
    print(f"Test {i}: {question}")
    print("=" * 70)
    
    # TF-IDF
    print("\n[TF-IDF Embeddings]")
    start = time.time()
    tfidf_results = tfidf_selector.select_top_k(question, k=3)
    tfidf_time = (time.time() - start) * 1000
    
    print(f"Time: {tfidf_time:.2f}ms")
    print("Top 3 matches:")
    for j, ex in enumerate(tfidf_results, 1):
        print(f"  {j}. {ex['question'][:60]}...")
    
    # Neural (if available)
    if use_neural:
        print("\n[Neural Embeddings]")
        start = time.time()
        neural_results = neural_selector.select_top_k(question, k=3)
        neural_time = (time.time() - start) * 1000
        
        print(f"Time: {neural_time:.2f}ms")
        print("Top 3 matches:")
        for j, ex in enumerate(neural_results, 1):
            score = ex.get('similarity_score', 0)
            print(f"  {j}. {ex['question'][:60]}... (score: {score:.3f})")
        
        print(f"\nSpeed difference: Neural is {neural_time/tfidf_time:.1f}x slower")
    
    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nTF-IDF Embeddings:")
print("  ✓ Very fast (1-2ms)")
print("  ✓ No external models")
print("  ✓ Good for exact keyword matching")
print("  ✗ Misses synonyms and paraphrasing")

if use_neural:
    print("\nNeural Embeddings:")
    print("  ✓ Better semantic understanding")
    print("  ✓ Handles synonyms and paraphrasing")
    print("  ✓ More robust to variations")
    print("  ✗ Slower (50-100ms)")
    print("  ✗ Requires model download (~100MB)")
    
    print("\nRecommendation:")
    print("  • Use TF-IDF for: Speed, simplicity, exact matching")
    print("  • Use Neural for: Accuracy, semantic similarity, robustness")
else:
    print("\nTo test Neural embeddings:")
    print("  1. Ensure sentence-transformers is installed: uv add sentence-transformers")
    print("  2. Use the neural selector in your code")
    print("  3. Re-run this test")

print("\n" + "=" * 70)


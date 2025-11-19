# Cache Strategies Guide

## Current Strategy: Question + Schema

### How It Works

```python
# Current implementation (graph_rag_workflow.py, line 239)
cache_key = f"{question}|{schema_str}"
```

**Cache Hit Requires:**
1. ✅ Exact question match
2. ✅ Same pruned schema

---

## Alternative Strategies

### Strategy 1: Question-Only Caching (Higher Hit Rate)

**Implementation:**

```python
# In graph_rag_workflow.py, change line 239:
# From:
cache_key = f"{question}|{schema_str}"

# To:
cache_key = question  # Just the question
hashed_key = lru_cache_manager._hash(cache_key)
```

**Pros:**
- ✅ Higher hit rate (50-80% vs 30-50%)
- ✅ Ignores schema pruning variations
- ✅ Simpler logic

**Cons:**
- ❌ Less accurate if schema actually matters
- ❌ Could return wrong answer if schema changes

**Use When:**
- Schema is stable
- Same question always needs same data
- Hit rate is more important than accuracy

---

### Strategy 2: Semantic Caching (Best for Paraphrasing)

**Implementation:**

```python
# Use embeddings to match similar questions
def get_semantic_cache_hit(question, cache, threshold=0.95):
    question_embedding = model.encode(question)
    
    for cached_key, cached_data in cache.items():
        if 'embedding' in cached_data:
            similarity = cosine_similarity(
                question_embedding,
                cached_data['embedding']
            )
            if similarity > threshold:
                return cached_data['answer']
    
    return None
```

**Pros:**
- ✅ Matches paraphrased questions
- ✅ "Who won Physics?" matches "Which scholars won prizes in Physics?"
- ✅ Much higher effective hit rate

**Cons:**
- ❌ More complex
- ❌ Slower (embedding computation)
- ❌ Risk of false matches

**Use When:**
- Users rephrase questions often
- You want maximum cache efficiency
- You can tolerate ~5% false matches

---

### Strategy 3: Hybrid Caching (Best of Both)

**Implementation:**

```python
# Try question-only first, then question+schema
def get_cached_answer(question, schema, cache):
    # Fast path: question-only
    simple_key = hash(question)
    if simple_key in cache:
        return cache[simple_key]
    
    # Accurate path: question + schema
    detailed_key = hash(f"{question}|{schema}")
    if detailed_key in cache:
        return cache[detailed_key]
    
    return None
```

**Pros:**
- ✅ High hit rate for repeated questions
- ✅ Accurate for schema-sensitive queries
- ✅ Best of both worlds

**Cons:**
- ❌ More memory (two cache entries per query)
- ❌ More complex logic

---

## Comparison Table

| Strategy | Hit Rate | Accuracy | Speed | Complexity | Memory |
|----------|----------|----------|-------|------------|--------|
| **Current** (Q+Schema) | 30-50% | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | Simple | Low |
| **Question-Only** | 50-80% | ⭐⭐⭐ | ⚡⚡⚡ | Simplest | Low |
| **Semantic** | 70-90% | ⭐⭐⭐⭐ | ⚡⚡ | Complex | Medium |
| **Hybrid** | 60-85% | ⭐⭐⭐⭐⭐ | ⚡⚡ | Moderate | High |

---

## Recommendation by Use Case

### For Your Project (Nobel Prize Data)

**Current Strategy (Q+Schema) is good because:**
- Schema pruning matters (Physics vs Chemistry needs different data)
- Accuracy is important for academic data
- Database is small (queries are fast anyway)

**Consider Question-Only if:**
- You're getting too many cache misses
- Schema pruning is too unpredictable
- Hit rate < 30% in your benchmarks

---

## How to Switch Strategies

### Switch to Question-Only

```python
# graph_rag_workflow.py, line 239
# Change from:
cache_key = f"{question}|{schema_str}"

# To:
cache_key = question
```

### Switch to Normalized Questions

```python
# Normalize before caching
def normalize_question(q):
    return q.lower().strip().rstrip('?!.')

cache_key = normalize_question(question)
```

This helps with:
- "Which scholars won prizes in Physics?" 
- "which scholars won prizes in physics" 
- "Which scholars won prizes in Physics??" 
→ All become same cache key!

---

## Monitoring Your Strategy

### Check Hit Rate

```python
# In BenchmarkStats.get_report()
hit_rate = (self.cache_hits / self.total_queries) * 100

# Good hit rates by strategy:
# Question+Schema: 30-50% = good
# Question-Only:   50-80% = good
# Semantic:        70-90% = good
```

### When to Change Strategy

**Switch from Current to Question-Only if:**
- Hit rate < 30%
- Schema pruning varies too much
- Most questions are repeated exactly

**Switch to Semantic if:**
- Users rephrase a lot
- Hit rate < 40% with question-only
- You want maximum efficiency

---

## Implementation Examples

### Example 1: Make Cache Case-Insensitive

```python
# graph_rag_workflow.py
cache_key = f"{question.lower()}|{schema_str}"
```

Now these match:
- "Which scholars won prizes in Physics?"
- "which scholars won prizes in physics?"
✅ Both hit cache!

### Example 2: Strip Punctuation

```python
import re

def normalize_question(q):
    # Remove extra punctuation
    q = re.sub(r'[?!.]+$', '', q.strip())
    return q.lower()

cache_key = f"{normalize_question(question)}|{schema_str}"
```

Now these match:
- "Which scholars won prizes in Physics?"
- "Which scholars won prizes in Physics??"
- "Which scholars won prizes in Physics"
✅ All hit cache!

### Example 3: Schema-Independent Questions

```python
# For questions that don't need specific schema
simple_questions = [
    "list all scholars",
    "count prizes",
    "show categories"
]

if any(pattern in question.lower() for pattern in simple_questions):
    cache_key = question  # Schema-independent
else:
    cache_key = f"{question}|{schema_str}"  # Schema-dependent
```

---

## Testing Different Strategies

```python
# test_cache_strategies.py
questions = [
    "Which scholars won prizes in Physics?",
    "which scholars won prizes in physics?",  # Case difference
    "Which scholars won prizes in Physics??",  # Punctuation
    "Who won Physics prizes?",                  # Paraphrase
]

# Test 1: Current strategy (exact match)
print("Current Strategy (Q+Schema):")
for i, q in enumerate(questions):
    if i == 0:
        cache_result = "MISS"
    else:
        cache_result = "HIT" if q == questions[0] else "MISS"
    print(f"  {q}: {cache_result}")

# Test 2: Normalized strategy
print("\nNormalized Strategy:")
normalized = [q.lower().rstrip('?!.') for q in questions]
for i, (q, norm) in enumerate(zip(questions, normalized)):
    cache_result = "HIT" if i > 0 and norm == normalized[0] else "MISS"
    print(f"  {q}: {cache_result}")
```

Output:
```
Current Strategy (Q+Schema):
  Which scholars won prizes in Physics?: MISS
  which scholars won prizes in physics?: MISS
  Which scholars won prizes in Physics??: MISS
  Who won Physics prizes?: MISS

Normalized Strategy:
  Which scholars won prizes in Physics?: MISS
  which scholars won prizes in physics?: HIT
  Which scholars won prizes in Physics??: HIT
  Who won Physics prizes?: MISS
```

---

## Summary

**Current Strategy:**
- ✅ Most accurate
- ✅ Respects schema context
- ❌ Lower hit rate (30-50%)

**To increase hit rate:**
1. **Easy**: Make case-insensitive
2. **Medium**: Question-only caching
3. **Advanced**: Semantic caching

**Start with**: Current strategy (already good!)  
**Optimize if**: Hit rate < 30% in your benchmarks

Check your hit rate with:
```bash
python graph_rag_workflow.py
# Ask same question twice, type 'stats'
```


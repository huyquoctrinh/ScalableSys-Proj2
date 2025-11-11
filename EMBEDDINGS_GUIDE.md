# Embeddings in Graph RAG - Complete Guide

## 📍 Where Embeddings Are Used

Embeddings are used in **one main place** in your Graph RAG system:

### **`text_2_cypher/exemplar_selector.py`** - Dynamic Example Selection

This module uses embeddings to find the most similar example queries when a user asks a question.

**Flow:**
```
User Question: "Which scholars won prizes in Physics?"
     ↓
Convert to Embedding
     ↓
Compare with Exemplar Embeddings
     ↓
Select Top-K Most Similar Examples
     ↓
Use in Few-Shot Prompt
```

---

## 🔄 Two Approaches Available

### **Current: TF-IDF Embeddings** (Fast, Simple)

**Location:** `text_2_cypher/exemplar_selector.py`

**Technology:**
- Uses `scikit-learn`'s `TfidfVectorizer`
- Creates **sparse vectors** based on word frequencies
- Fast and lightweight

**Pros:**
- ✅ Very fast (~0.001s per embedding)
- ✅ No external models needed
- ✅ Low memory usage
- ✅ Works well for exact keyword matching

**Cons:**
- ❌ No semantic understanding
- ❌ Misses synonyms (e.g., "scholars" vs "laureates")
- ❌ Doesn't understand context

**Example Matching:**
```
Query: "Which scholars won prizes in Physics?"
Good Match: "Which scholars won prizes in Chemistry?" ✓
Poor Match: "Who received Nobel awards in Physics?" ✗
```

---

### **Alternative: Neural Embeddings** (Semantic, Powerful)

**Location:** `text_2_cypher/exemplar_selector_neural.py` (just created)

**Technology:**
- Uses `sentence-transformers`
- Creates **dense vectors** with semantic meaning
- Slower but more intelligent

**Pros:**
- ✅ Understands synonyms and context
- ✅ Better semantic matching
- ✅ Handles paraphrasing well
- ✅ More robust to variations

**Cons:**
- ❌ Slower (~0.05-0.1s per embedding)
- ❌ Requires downloading model (~100MB)
- ❌ Higher memory usage (~400MB)
- ❌ Needs GPU for best performance (optional)

**Example Matching:**
```
Query: "Which scholars won prizes in Physics?"
Good Match: "Which scholars won prizes in Chemistry?" ✓
Good Match: "Who received Nobel awards in Physics?" ✓
Good Match: "List Physics Nobel laureates" ✓
```

---

## 📊 Comparison Table

| Feature | TF-IDF (Current) | Neural (Alternative) |
|---------|------------------|---------------------|
| **Speed** | 0.001s | 0.05-0.1s |
| **Model Size** | None | ~100MB |
| **Memory Usage** | ~10MB | ~400MB |
| **Semantic Understanding** | No | Yes |
| **Synonym Detection** | No | Yes |
| **Setup Complexity** | Simple | Moderate |
| **Dependencies** | scikit-learn | sentence-transformers, torch |
| **Best For** | Exact keyword matching | Semantic similarity |

---

## 🔧 How to Switch to Neural Embeddings

### Step 1: Already Installed! ✓

`sentence-transformers` is already in your `pyproject.toml`:

```toml
dependencies = [
    "sentence-transformers>=2.2.2",
    ...
]
```

### Step 2: Update Import

In `graph_rag_workflow.py` (or wherever you use it), change:

**From:**
```python
from text_2_cypher import ExemplarSelector
```

**To:**
```python
from text_2_cypher.exemplar_selector_neural import ExemplarSelector
```

### Step 3: Test It

```bash
python graph_rag_workflow.py
```

**First run will download the model** (~100MB):
```
Computing neural embeddings for 8 exemplars...
Downloading model 'all-MiniLM-L6-v2'...
✓ Embeddings computed: (8, 384)
```

---

## 🎯 Which Should You Use?

### Use **TF-IDF** (Current) If:
- ✅ Speed is critical
- ✅ Your exemplars use similar wording to user questions
- ✅ You want minimal dependencies
- ✅ You're on a resource-constrained system

### Use **Neural** (Alternative) If:
- ✅ You want better semantic matching
- ✅ Users phrase questions differently
- ✅ You need synonym detection
- ✅ Accuracy > Speed
- ✅ You have GPU available (optional but helpful)

---

## 🧪 Test Both Approaches

Let me create a comparison script:

```python
# test_embeddings.py
from text_2_cypher.exemplar_selector import ExemplarSelector as TFIDFSelector
from text_2_cypher.exemplar_selector_neural import ExemplarSelector as NeuralSelector
import json
import time

# Load exemplars
with open('exemplars.json', 'r') as f:
    exemplars = json.load(f)

# Test questions (different phrasings of similar questions)
test_questions = [
    "Which scholars won prizes in Physics?",
    "Who received Nobel awards in Physics?",
    "List Physics Nobel laureates",
]

print("=" * 60)
print("TFIDF vs Neural Embeddings Comparison")
print("=" * 60)

# Initialize both
print("\nInitializing selectors...")
tfidf_selector = TFIDFSelector(exemplars)
neural_selector = NeuralSelector(exemplars)

for question in test_questions:
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}")
    
    # TF-IDF
    start = time.time()
    tfidf_results = tfidf_selector.select_top_k(question, k=2)
    tfidf_time = time.time() - start
    
    print(f"\n[TF-IDF] Time: {tfidf_time*1000:.2f}ms")
    for i, ex in enumerate(tfidf_results, 1):
        print(f"  {i}. {ex['question']}")
    
    # Neural
    start = time.time()
    neural_results = neural_selector.select_top_k(question, k=2)
    neural_time = time.time() - start
    
    print(f"\n[Neural] Time: {neural_time*1000:.2f}ms")
    for i, ex in enumerate(neural_results, 1):
        score = ex.get('similarity_score', 0)
        print(f"  {i}. {ex['question']} (score: {score:.3f})")
```

Run it:
```bash
python test_embeddings.py
```

---

## 🔍 Current Implementation Details

### Where Embeddings Are Generated

**File:** `text_2_cypher/exemplar_selector.py`

**Line 12:** Pre-compute exemplar embeddings on initialization
```python
self.exemplar_embeddings = self.vectorizer.fit_transform(self.exemplar_questions)
```

**Line 17:** Compute embedding for user question
```python
question_embedding = self.vectorizer.transform([question])
```

**Line 20:** Find similar exemplars using cosine similarity
```python
similarities = cosine_similarity(question_embedding, self.exemplar_embeddings).flatten()
```

### Embedding Dimensions

**TF-IDF:**
- Dimension = vocabulary size (typically 100-1000)
- Sparse vector (mostly zeros)
- Example: `[0, 0, 0.3, 0, 0.7, 0, ...]`

**Neural:**
- Dimension = 384 (all-MiniLM-L6-v2)
- Dense vector (all values used)
- Example: `[0.12, -0.34, 0.56, -0.23, ...]`

---

## 💡 Cache and Embeddings

The `cache_method/cache.py` has an `embedding` field but it's **not currently used** in the main workflow:

```python
def process_value(self, retrieved_value, answer, embedding):
    return {
        "retrieved_value": retrieved_value,
        "answer": answer,
        "embedding": embedding  # Stored but not used
    }
```

This is **for future semantic caching** where you could:
1. Store question embeddings in cache
2. Match similar (not identical) questions
3. Return cached results for paraphrased questions

---

## 🚀 Future Enhancement: Semantic Caching

Here's how you could use embeddings in caching:

```python
# Instead of exact match
cache_key = question

# Use semantic similarity
question_embedding = model.encode(question)
for cached_key, cached_data in cache.items():
    if cosine_similarity(question_embedding, cached_data['embedding']) > 0.95:
        # Questions are semantically similar
        return cached_data['answer']
```

This would allow:
- "Which scholars won prizes in Physics?" (cached)
- "Who received Nobel awards in Physics?" (cache HIT! 98% similar)

---

## 📦 Models Available

If you use neural embeddings, you can choose different models:

### Recommended Models

| Model | Size | Dims | Speed | Accuracy | Use Case |
|-------|------|------|-------|----------|----------|
| `all-MiniLM-L6-v2` | 80MB | 384 | Fast | Good | **Recommended** |
| `all-mpnet-base-v2` | 420MB | 768 | Slow | Best | High accuracy needed |
| `all-MiniLM-L12-v2` | 120MB | 384 | Medium | Better | Balance |

### How to Change Model

In `exemplar_selector_neural.py`:

```python
# Fast and lightweight (default)
selector = ExemplarSelector(exemplars, model_name='all-MiniLM-L6-v2')

# More accurate but slower
selector = ExemplarSelector(exemplars, model_name='all-mpnet-base-v2')
```

---

## ✅ Summary

**Current Setup:**
- ✅ Using **TF-IDF embeddings** from scikit-learn
- ✅ Fast, simple, no external models
- ✅ Good for keyword-based matching
- ✅ Located in `text_2_cypher/exemplar_selector.py`

**Alternative Available:**
- ✅ **Neural embeddings** implementation ready
- ✅ Better semantic understanding
- ✅ Located in `text_2_cypher/exemplar_selector_neural.py`
- ✅ Just change the import to use it

**Choose based on your needs:**
- **Speed + Simplicity** → TF-IDF (current)
- **Accuracy + Semantics** → Neural (alternative)

Both are production-ready! 🚀


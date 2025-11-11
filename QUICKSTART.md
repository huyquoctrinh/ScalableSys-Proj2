# Quick Start Guide

Get your GraphRAG system running in 5 minutes! ⚡

## Prerequisites

- Python 3.13+
- `uv` package manager
- Docker (for Kuzu database)

## Setup Steps

### 1️⃣ Install Dependencies (30 seconds)

```bash
uv sync
```

### 2️⃣ Get OpenRouter API Key (2 minutes)

1. Go to https://openrouter.ai/
2. Sign up (free tier available)
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy your API key

### 3️⃣ Create `.env` File (10 seconds)

In the project root, create a `.env` file:

```bash
echo "OPENROUTER_API_KEY=your_actual_key_here" > .env
```

Or manually create `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 4️⃣ Start Kuzu Database (30 seconds)

```bash
docker compose up -d
```

Verify it's running: Open http://localhost:8000 in your browser

### 5️⃣ Run the Application (10 seconds)

**Option A: Main Graph RAG App**
```bash
uv run marimo run graph_rag.py
```

**Option B: Advanced Demo (with all enhancements)**
```bash
uv run marimo run advanced_demo_workflow.py
```

**Option C: Basic Demo**
```bash
uv run marimo run demo_workflow.py
```

## ✅ Verify Everything Works

### Test 1: Check API Key

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key Loaded' if os.getenv('OPENROUTER_API_KEY') else '✗ Missing API Key')"
```

**Expected output:** `✓ API Key Loaded`

### Test 2: Check Cache

```bash
python -c "from cache_method import LRUDataManager; c = LRUDataManager(10); c.set_data('test', 'works'); print('✓ Cache Works' if c.get_data('test') == 'works' else '✗ Cache Error')"
```

**Expected output:** `✓ Cache Works`

### Test 3: Run Tests

```bash
pytest test/test_lru_cache.py -v
```

**Expected:** All tests pass ✓

## 🎯 Try Your First Query

Once the app is running:

1. Enter a question like:
   - "Which scholars won prizes in Physics?"
   - "Who was affiliated with University of Cambridge?"
   - "How many laureates won prizes in Chemistry?"

2. Watch the console for cache indicators:
   - First time: `✗ Cache miss. Generating new query...`
   - Second time: `✓ Cache hit! Using cached query and results.`

3. Notice the speed difference! 🚀

## 📊 Understanding the Output

### Console Output Explained

```
✗ Cache miss. Generating new query...
✓ Query valid after 2 iteration(s)
✓ Query cached. Cache size: 1/256
```

- **Cache miss**: Generating query for the first time
- **2 iterations**: Self-refinement took 2 attempts to get valid query
- **Cache size 1/256**: Cache now has 1 entry, can hold up to 256

### Marimo UI

- **Query**: The generated Cypher query
- **Answer**: Natural language response
- **Post-processing rules**: Any cleanup applied
- **Cache status**: HIT or MISS

## 🐛 Troubleshooting

### Problem: "API key not found"

**Solution:**
```bash
# Check .env file exists
cat .env

# Make sure it's in the project root
pwd
ls -la .env
```

### Problem: "Cannot connect to Kuzu"

**Solution:**
```bash
# Restart Docker container
docker compose down
docker compose up -d

# Check if it's running
docker ps | grep kuzu
```

### Problem: "Module not found"

**Solution:**
```bash
# Reinstall dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Problem: Cache not working

**Check:**
1. Are you asking the EXACT same question?
2. Cache is reset each time you restart the app
3. Cache uses question + schema, so schema changes = cache miss

## 📚 Next Steps

### Learn More

- **[ENV_CONFIG.md](ENV_CONFIG.md)** - Detailed configuration options
- **[CACHE_INTEGRATION.md](CACHE_INTEGRATION.md)** - How caching works
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Complete integration guide
- **[STRUCTURE.md](STRUCTURE.md)** - Project architecture
- **[task1.md](task1.md)** - Text2Cypher enhancements

### Explore the Code

- **`graph_rag.py`** - Main application with full integration
- **`cache_method/`** - LRU cache implementation
- **`text_2_cypher/`** - Query generation enhancements
- **`advanced_demo_workflow.py`** - Complete workflow demo

### Customize

**Change LLM model:**
```python
# In graph_rag.py, line ~126
lm = dspy.LM(
    model="openrouter/anthropic/claude-3.5-sonnet",  # Different model
    api_base="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
```

**Adjust cache size:**
```python
# In graph_rag.py, line ~37
cache_manager = LRUDataManager(cache_size=512)  # Bigger cache
```

**Add more exemplars:**
```python
# In graph_rag.py, lines ~222-248
exemplars = [
    # Add your own question-cypher pairs
    {
        "question": "Your question here",
        "cypher": "Your Cypher query here",
        "category": "category_name"
    },
]
```

## 🎓 Example Questions to Try

**Simple queries:**
- "List all female laureates"
- "Which prizes did Marie Curie win?"
- "How many scholars won prizes in Physics?"

**Complex queries:**
- "Which Physics laureates were born in the United States?"
- "List scholars affiliated with MIT who won prizes after 2000"
- "How many prizes were awarded in Chemistry between 1950 and 2000?"

**Aggregations:**
- "What is the average prize amount?"
- "Count laureates by country"
- "Show prize distribution by category"

## 🚀 Performance Tips

1. **Warm up the cache**: Run common queries once
2. **Monitor cache size**: Check if you need more/less capacity
3. **Use the same phrasing**: Cache is exact-match on questions
4. **Batch similar questions**: Process related queries together

## 💡 Pro Tips

- **Cache hits = faster + cheaper**: Each hit saves ~7 seconds and $0.002
- **Schema pruning is smart**: It removes irrelevant parts automatically
- **Refinement loop is powerful**: Most queries succeed in 1-2 iterations
- **Post-processing catches common mistakes**: Makes queries more robust

## ✨ You're All Set!

Your GraphRAG system is now:
- ✅ Using OpenRouter for LLM inference
- ✅ Caching queries with LRU strategy
- ✅ Self-refining queries for accuracy
- ✅ Post-processing for robustness
- ✅ Ready for production use!

**Happy querying! 🎉**

---

Need help? Check the [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) or [ENV_CONFIG.md](ENV_CONFIG.md) for detailed documentation.



# Database Retrieval Logging Guide

## 📝 Overview

The Graph RAG workflow now includes comprehensive logging for all database interactions, providing detailed insights into:
- Database query execution
- Retrieved data
- Performance metrics
- Cache behavior
- Errors and debugging info

## 📁 Log Files

### 1. **`graph_rag_detailed.log`** (New - Detailed Technical Log)
Technical log with structured information about database operations.

**Contents:**
- Timestamp for every operation
- Database query execution details
- Retrieved rows and columns
- Sample data from results
- Performance breakdown
- Cache hits/misses
- Error traces

### 2. **`chat_log.txt`** (Existing - User-Friendly Log)
Human-readable session log with questions, answers, and benchmarks.

**Contents:**
- User questions
- Generated answers
- Cache statistics
- Session timestamps

---

## 🔍 What Gets Logged

### Database Query Execution

Every database query logs:

```
============================================================
DATABASE QUERY EXECUTION
============================================================
Question: Which scholars won prizes in Physics?
Cypher Query: MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName
✓ Query executed successfully in 0.234s
Number of rows retrieved: 238
Number of values: 238
Column names: ['knownName']
Sample results (first 5 rows):
  Row 1: ['Albert Einstein']
  Row 2: ['Marie Curie']
  Row 3: ['Niels Bohr']
  Row 4: ['Werner Heisenberg']
  Row 5: ['Erwin Schrödinger']
  ... and 233 more rows
Full context for answer generation: ['Albert Einstein', 'Marie Curie', ...]
```

### Cache Hits

Cache hits log minimal information (no DB query):

```
============================================================
CACHE HIT - Skipping database query
============================================================
Question: Which scholars won prizes in Physics?
Cache key: a3f5b2c9d4e1f2a3...
Response time: 0.012s
Cached answer: The scholars who won prizes in Physics include...
Cache size: 5/128
============================================================
```

### Performance Breakdown

After each query, performance metrics are logged:

```
============================================================
PERFORMANCE BREAKDOWN
============================================================
Database query time: 0.234s
Answer generation time: 2.456s
Total processing time: 8.134s
Cache size: 5/128
============================================================
```

### Error Logging

When queries fail, detailed error information is captured:

```
✗ Query execution failed after 0.123s
Error type: RuntimeError
Error message: Binder exception: Referenced property name does not exist
Failed query: MATCH (s:Scholar) WHERE s.invalid_field = 'test' RETURN s
```

---

## 📊 Log Format

### Log Entry Structure

```
<timestamp> - <module> - <level> - <message>

2025-01-15 14:23:45,123 - __main__ - INFO - DATABASE QUERY EXECUTION
```

**Components:**
- **Timestamp**: When the event occurred
- **Module**: Source of the log (`__main__`)
- **Level**: Log severity (INFO, WARNING, ERROR)
- **Message**: Detailed information

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| `INFO` | Normal operations | Query executed successfully |
| `WARNING` | Non-critical issues | No context for answer generation |
| `ERROR` | Failures | Query execution failed |

---

## 🔍 Analyzing Logs

### Find Slow Queries

```bash
# Find queries taking > 1 second
grep "Query executed successfully" graph_rag_detailed.log | grep -E "[1-9]\.[0-9]{3}s"
```

### Check Cache Performance

```bash
# Count cache hits vs misses
grep "CACHE HIT" graph_rag_detailed.log | wc -l
grep "DATABASE QUERY EXECUTION" graph_rag_detailed.log | wc -l
```

### Find Errors

```bash
# View all errors
grep "ERROR" graph_rag_detailed.log

# View failed queries
grep "Failed query:" graph_rag_detailed.log
```

### See Retrieved Data

```bash
# View all database results
grep "Full context for answer generation:" graph_rag_detailed.log
```

---

## 📈 Example Log Session

### Complete Example

```log
2025-01-15 14:23:45,123 - __main__ - INFO - ============================================================
2025-01-15 14:23:45,123 - __main__ - INFO - DATABASE QUERY EXECUTION
2025-01-15 14:23:45,123 - __main__ - INFO - ============================================================
2025-01-15 14:23:45,123 - __main__ - INFO - Question: Which scholars won prizes in Physics?
2025-01-15 14:23:45,124 - __main__ - INFO - Cypher Query: MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName
2025-01-15 14:23:45,358 - __main__ - INFO - ✓ Query executed successfully in 0.234s
2025-01-15 14:23:45,359 - __main__ - INFO - Number of rows retrieved: 238
2025-01-15 14:23:45,359 - __main__ - INFO - Number of values: 238
2025-01-15 14:23:45,359 - __main__ - INFO - Column names: ['knownName']
2025-01-15 14:23:45,359 - __main__ - INFO - Sample results (first 5 rows):
2025-01-15 14:23:45,359 - __main__ - INFO -   Row 1: ['Albert Einstein']
2025-01-15 14:23:45,359 - __main__ - INFO -   Row 2: ['Marie Curie']
2025-01-15 14:23:45,359 - __main__ - INFO -   Row 3: ['Niels Bohr']
2025-01-15 14:23:45,360 - __main__ - INFO -   Row 4: ['Werner Heisenberg']
2025-01-15 14:23:45,360 - __main__ - INFO -   Row 5: ['Erwin Schrödinger']
2025-01-15 14:23:45,360 - __main__ - INFO -   ... and 233 more rows
2025-01-15 14:23:45,360 - __main__ - INFO - Full context for answer generation: ['Albert Einstein', 'Marie Curie', ...]
2025-01-15 14:23:45,361 - __main__ - INFO - Generating natural language answer from context...
2025-01-15 14:23:47,817 - __main__ - INFO - ✓ Answer generated in 2.456s
2025-01-15 14:23:47,817 - __main__ - INFO - Answer length: 342 characters
2025-01-15 14:23:47,818 - __main__ - INFO - Final Answer: The scholars who won prizes in Physics include...
2025-01-15 14:23:47,818 - __main__ - INFO - ✓ Answer cached with key: a3f5b2c9d4e1f2a3...
2025-01-15 14:23:47,818 - __main__ - INFO - ============================================================
2025-01-15 14:23:47,818 - __main__ - INFO - PERFORMANCE BREAKDOWN
2025-01-15 14:23:47,818 - __main__ - INFO - ============================================================
2025-01-15 14:23:47,819 - __main__ - INFO - Database query time: 0.234s
2025-01-15 14:23:47,819 - __main__ - INFO - Answer generation time: 2.456s
2025-01-15 14:23:47,819 - __main__ - INFO - Total processing time: 8.134s
2025-01-15 14:23:47,819 - __main__ - INFO - Cache size: 1/128
2025-01-15 14:23:47,819 - __main__ - INFO - ============================================================
```

---

## 🛠️ Configuration

### Change Log Level

In `graph_rag_workflow.py`, line 19:

```python
# Current: INFO level (shows all operations)
logging.basicConfig(level=logging.INFO, ...)

# For debugging: Show even more details
logging.basicConfig(level=logging.DEBUG, ...)

# For production: Only warnings and errors
logging.basicConfig(level=logging.WARNING, ...)
```

### Change Log File Location

In `graph_rag_workflow.py`, line 22:

```python
# Current
handlers=[
    logging.FileHandler('graph_rag_detailed.log', encoding='utf-8'),
    logging.StreamHandler()
]

# Custom location
handlers=[
    logging.FileHandler('/path/to/my/logs/app.log', encoding='utf-8'),
    logging.StreamHandler()
]
```

### Disable Console Output

Keep file logging only:

```python
handlers=[
    logging.FileHandler('graph_rag_detailed.log', encoding='utf-8'),
    # Remove StreamHandler() to disable console output
]
```

---

## 📊 Log Analysis Scripts

### Analyze Performance

```python
# analyze_logs.py
import re
from collections import defaultdict

with open('graph_rag_detailed.log', 'r') as f:
    content = f.read()

# Extract query times
query_times = re.findall(r'Database query time: ([\d.]+)s', content)
query_times = [float(t) for t in query_times]

print(f"Total queries: {len(query_times)}")
print(f"Average query time: {sum(query_times) / len(query_times):.3f}s")
print(f"Min query time: {min(query_times):.3f}s")
print(f"Max query time: {max(query_times):.3f}s")

# Count rows retrieved
rows = re.findall(r'Number of rows retrieved: (\d+)', content)
rows = [int(r) for r in rows]

print(f"\nAverage rows retrieved: {sum(rows) / len(rows):.1f}")
print(f"Max rows retrieved: {max(rows)}")
```

### Extract All Retrieved Data

```python
# extract_data.py
import re

with open('graph_rag_detailed.log', 'r') as f:
    content = f.read()

# Find all database results
results = re.findall(r'Full context for answer generation: (.+)', content)

for i, result in enumerate(results, 1):
    print(f"\nQuery {i} results:")
    print(result[:200] + "..." if len(result) > 200 else result)
```

---

## 🔐 Security Note

**Warning:** Logs contain actual data from your database!

- ✅ **Safe**: Store logs in secure location
- ✅ **Safe**: Restrict log file permissions
- ❌ **Avoid**: Committing logs to version control
- ❌ **Avoid**: Sharing logs publicly

Add to `.gitignore`:
```
*.log
graph_rag_detailed.log
chat_log.txt
```

---

## 📋 Log Rotation

For production, implement log rotation:

```python
from logging.handlers import RotatingFileHandler

# Rotate after 10MB, keep 5 backups
handler = RotatingFileHandler(
    'graph_rag_detailed.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)
```

---

## 🎯 Use Cases

### Debugging Query Issues

When a query fails, check the log for:
- The exact Cypher query that failed
- The error message
- The question that triggered it

```bash
grep -A 5 "Query execution failed" graph_rag_detailed.log
```

### Performance Optimization

Identify slow operations:
```bash
# Find queries taking > 0.5s
grep "Database query time" graph_rag_detailed.log | awk '{if ($6 > 0.5) print}'
```

### Data Analysis

Understand what data is being retrieved:
```bash
# See what columns are being returned
grep "Column names:" graph_rag_detailed.log | sort | uniq -c
```

### Cache Effectiveness

Monitor cache performance:
```bash
# Cache hit rate
hits=$(grep -c "CACHE HIT" graph_rag_detailed.log)
total=$(grep -c "Question:" graph_rag_detailed.log)
echo "Cache hit rate: $(echo "scale=2; $hits * 100 / $total" | bc)%"
```

---

## ✅ Summary

The enhanced logging provides:

✅ **Complete visibility** into database operations  
✅ **Performance metrics** for optimization  
✅ **Error tracking** for debugging  
✅ **Data insights** for analysis  
✅ **Cache monitoring** for effectiveness  
✅ **Audit trail** for compliance  

**Log files:**
- `graph_rag_detailed.log` - Technical details
- `chat_log.txt` - User session

**Key features:**
- Automatic logging (no manual calls needed)
- Structured format for parsing
- Sample data preview (first 5 rows)
- Performance breakdowns
- Error details with stack traces

Start using it - just run `python graph_rag_workflow.py` and check the logs! 📊


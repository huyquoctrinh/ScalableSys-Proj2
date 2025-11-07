# Task 1: Text2Cypher Improvement - Implementation Guide

## Overview

Task 1 focuses on enhancing the Text2Cypher component of the GraphRAG pipeline to generate more accurate and robust Cypher queries. This involves three main enhancements that work together to improve query generation quality.

**Goal**: Improve the accuracy and reliability of natural language to Cypher query translation.

---

## Sub-Task 1.1: Dynamic Few-Shot Exemplar Selection

### Objective
Instead of using static examples or no examples, dynamically select the most relevant example queries based on similarity to the user's input question.

### Why This Matters
Few-shot learning helps the LLM understand the query pattern better by showing similar examples. Dynamic selection ensures the examples are actually relevant to the current question.

### Implementation Steps

#### 1. Create an Exemplar Dataset

Build a collection of high-quality question-Cypher pairs covering diverse query patterns:

```python
exemplars = [
    {
        "question": "Which scholars won prizes in Physics?",
        "cypher": "MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName",
        "category": "simple_filter"
    },
    {
        "question": "Who was affiliated with University of Cambridge?",
        "cypher": "MATCH (s:Scholar)-[:AFFILIATED_WITH]->(i:Institution) WHERE LOWER(i.name) CONTAINS 'cambridge' RETURN s.knownName",
        "category": "institution_affiliation"
    },
    {
        "question": "How many laureates won prizes in Chemistry between 1950 and 2000?",
        "cypher": "MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'chemistry' AND p.awardYear >= 1950 AND p.awardYear <= 2000 RETURN count(DISTINCT s)",
        "category": "aggregation_with_date_range"
    },
    {
        "question": "Which Physics laureates were born in the United States?",
        "cypher": "MATCH (s:Scholar)-[:WON]->(p:Prize), (s)-[:BORN_IN]->(c:City)-[:IS_CITY_IN]->(co:Country) WHERE LOWER(p.category) = 'physics' AND LOWER(co.name) CONTAINS 'united states' RETURN s.knownName, c.name",
        "category": "multi_hop"
    },
    {
        "question": "List all female laureates in Medicine",
        "cypher": "MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'medicine' AND LOWER(s.gender) = 'female' RETURN s.knownName, p.awardYear",
        "category": "gender_filter"
    },
    # Add 10-20 more diverse examples
]
```

**Categories to Cover:**
- Simple filters (single condition)
- Multiple conditions (AND/OR)
- Date/year range queries
- Aggregations (COUNT, SUM, AVG)
- Multi-hop path queries
- Relationship-based queries
- String matching (CONTAINS)
- Sorting (ORDER BY)
- Limiting results (LIMIT)

#### 2. Implement Similarity Scoring

**Option A: Using Sentence Embeddings (Recommended)**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class ExemplarSelector:
    def __init__(self, exemplars, model_name='all-MiniLM-L6-v2'):
        self.exemplars = exemplars
        self.model = SentenceTransformer(model_name)
        
        # Pre-compute embeddings for all exemplar questions
        self.exemplar_questions = [ex['question'] for ex in exemplars]
        self.exemplar_embeddings = self.model.encode(self.exemplar_questions)
    
    def select_top_k(self, question: str, k: int = 3) -> list[dict]:
        """Select top-k most similar exemplars"""
        # Encode the input question
        question_embedding = self.model.encode([question])[0]
        
        # Compute cosine similarity
        similarities = np.dot(self.exemplar_embeddings, question_embedding) / (
            np.linalg.norm(self.exemplar_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return selected exemplars
        return [self.exemplars[i] for i in top_k_indices]
```

**Option B: Using Simple Keyword Matching (Fallback)**

```python
from collections import Counter

def keyword_similarity(q1: str, q2: str) -> float:
    """Simple keyword-based similarity"""
    words1 = set(q1.lower().split())
    words2 = set(q2.lower().split())
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0
```

#### 3. Integrate with DSPy Text2Cypher

Modify your `Text2Cypher` signature to include examples:

```python
class Text2CypherWithExamples(dspy.Signature):
    """
    Translate the question into a valid Cypher query that respects the graph schema.
    Use the provided examples as reference for query patterns.
    
    <EXAMPLES>
    {examples}
    </EXAMPLES>
    
    <SYNTAX>
    - When matching on Scholar names, ALWAYS match on the `knownName` property
    - For countries, cities, continents and institutions, match on the `name` property
    - Use short, concise alphanumeric strings as variable names (e.g., `s1`, `p1`)
    - Always respect the relationship direction (FROM/TO) using schema information
    - When comparing string properties, ALWAYS:
      - Lowercase the property values before comparison
      - Use the WHERE clause
      - Use the CONTAINS operator for substring matching
    - DO NOT use APOC as the database does not support it
    </SYNTAX>
    
    <RETURN_RESULTS>
    - If the result is an integer, return it as an integer
    - Return property values rather than entire nodes or relationships
    - Do not coerce data types in results
    - NO Cypher keywords should be returned by your query
    </RETURN_RESULTS>
    """
    
    question: str = dspy.InputField()
    input_schema: str = dspy.InputField()
    examples: str = dspy.InputField()
    query: Query = dspy.OutputField()
```

**Usage:**

```python
def generate_query_with_examples(question, schema, exemplar_selector):
    # Select relevant examples
    selected_examples = exemplar_selector.select_top_k(question, k=3)
    
    # Format examples as string
    examples_text = "\n\n".join([
        f"Question: {ex['question']}\nCypher: {ex['cypher']}"
        for ex in selected_examples
    ])
    
    # Generate query
    text2cypher = dspy.Predict(Text2CypherWithExamples)
    result = text2cypher(
        question=question,
        input_schema=schema,
        examples=examples_text
    )
    
    return result.query
```

### Testing Dynamic Selection

```python
# Test cases
test_questions = [
    "Which scholars won prizes in Chemistry?",  # Should match physics example
    "How many Medicine laureates are there?",    # Should match count example
    "List laureates affiliated with MIT",        # Should match institution example
]

for q in test_questions:
    selected = exemplar_selector.select_top_k(q, k=3)
    print(f"\nQuestion: {q}")
    print("Top 3 similar examples:")
    for ex in selected:
        print(f"  - {ex['question']}")
```

---

## Sub-Task 1.2: Self-Refinement Loop

### Objective
Implement an iterative process that generates a query, validates it, and repairs it if validation fails.

### Why This Matters
LLMs can make syntax errors or misunderstand the schema. A refinement loop catches these errors and gives the model a chance to self-correct based on error feedback.

### Implementation Steps

#### 1. Create Query Validation Function

Use Kuzu's `EXPLAIN` command to check syntax without executing:

```python
def validate_cypher(conn: kuzu.Connection, query: str) -> tuple[bool, str | None]:
    """
    Validate a Cypher query using EXPLAIN.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # EXPLAIN checks syntax without executing
        conn.execute(f"EXPLAIN {query}")
        return True, None
    except RuntimeError as e:
        error_msg = str(e)
        return False, error_msg
    except Exception as e:
        return False, str(e)
```

#### 2. Create Repair Signature in DSPy

```python
class RepairCypher(dspy.Signature):
    """
    The previous Cypher query failed validation with an error.
    Analyze the error and generate a corrected version of the query.
    
    Common error patterns:
    - Syntax errors: missing parentheses, incorrect operators
    - Schema mismatches: wrong node/relationship labels, non-existent properties
    - Type errors: comparing incompatible types
    - Missing WHERE clauses for filters
    
    Fix the query while maintaining the original intent.
    """
    
    original_query: str = dspy.InputField(desc="The Cypher query that failed")
    error_message: str = dspy.InputField(desc="Error message from Kuzu")
    question: str = dspy.InputField(desc="Original user question")
    input_schema: str = dspy.InputField(desc="Graph schema")
    repaired_query: Query = dspy.OutputField(desc="Corrected Cypher query")
```

#### 3. Implement Refinement Loop

```python
class QueryGenerator:
    def __init__(self, conn, max_iterations=3):
        self.conn = conn
        self.max_iterations = max_iterations
        self.text2cypher = dspy.Predict(Text2Cypher)
        self.repair = dspy.Predict(RepairCypher)
    
    def generate_with_refinement(
        self, 
        question: str, 
        schema: str,
        examples: str = ""
    ) -> tuple[str, list[str]]:
        """
        Generate query with self-refinement.
        
        Returns:
            (final_query, history_of_queries)
        """
        query_history = []
        current_query = None
        
        for iteration in range(self.max_iterations):
            if iteration == 0:
                # Initial generation
                result = self.text2cypher(
                    question=question,
                    input_schema=schema,
                    examples=examples
                )
                current_query = result.query.query
            else:
                # Repair based on error
                result = self.repair(
                    original_query=current_query,
                    error_message=error_msg,
                    question=question,
                    input_schema=schema
                )
                current_query = result.repaired_query.query
            
            query_history.append(current_query)
            
            # Validate
            is_valid, error_msg = validate_cypher(self.conn, current_query)
            
            if is_valid:
                print(f"✓ Query valid after {iteration + 1} iteration(s)")
                return current_query, query_history
            else:
                print(f"✗ Iteration {iteration + 1} failed: {error_msg}")
        
        # Return last attempt even if not valid
        print(f"⚠ Max iterations reached. Returning last attempt.")
        return current_query, query_history
```

#### 4. Add Logging and Metrics

```python
class RefinementMetrics:
    def __init__(self):
        self.total_queries = 0
        self.valid_first_try = 0
        self.valid_after_refinement = 0
        self.failed_queries = 0
        self.avg_iterations = []
    
    def record(self, iterations: int, success: bool):
        self.total_queries += 1
        if iterations == 1 and success:
            self.valid_first_try += 1
        elif success:
            self.valid_after_refinement += 1
        else:
            self.failed_queries += 1
        self.avg_iterations.append(iterations)
    
    def report(self):
        print(f"\n=== Refinement Metrics ===")
        print(f"Total queries: {self.total_queries}")
        print(f"Valid on first try: {self.valid_first_try} ({self.valid_first_try/self.total_queries*100:.1f}%)")
        print(f"Valid after refinement: {self.valid_after_refinement} ({self.valid_after_refinement/self.total_queries*100:.1f}%)")
        print(f"Failed: {self.failed_queries} ({self.failed_queries/self.total_queries*100:.1f}%)")
        print(f"Avg iterations: {sum(self.avg_iterations)/len(self.avg_iterations):.2f}")
```

### Testing Self-Refinement

```python
# Test with queries that might have issues
test_cases = [
    {
        "question": "How many Physics laureates are there?",
        "expected_fix": "Should add DISTINCT or proper counting"
    },
    {
        "question": "Who won a prize at University of Cambridge?",
        "expected_fix": "Should use AFFILIATED_WITH relationship, not WON"
    }
]

metrics = RefinementMetrics()

for test in test_cases:
    query, history = generator.generate_with_refinement(
        question=test['question'],
        schema=schema_dict
    )
    print(f"\nFinal query: {query}")
    print(f"Iterations: {len(history)}")
    metrics.record(len(history), validate_cypher(conn, query)[0])

metrics.report()
```

---

## Sub-Task 1.3: Rule-Based Post-Processor

### Objective
Apply deterministic rules to fix common patterns and issues in generated queries.

### Why This Matters
LLMs may generate syntactically valid but semantically incorrect queries. Rule-based post-processing catches common mistakes that can be fixed with simple string manipulation.

### Implementation Steps

#### 1. Define Common Query Issues

Based on the project requirements and Kuzu specifics:

1. **String comparisons not using LOWER() and CONTAINS**
2. **Returning full nodes instead of properties**
3. **APOC function calls (not supported)**
4. **Incorrect property names**
5. **Missing relationship directions**
6. **Extra whitespace/newlines**

#### 2. Implement Post-Processing Rules

```python
import re

class CypherPostProcessor:
    def __init__(self):
        self.rules_applied = []
    
    def process(self, query: str) -> str:
        """Apply all post-processing rules"""
        self.rules_applied = []
        
        query = self.enforce_lowercase_contains(query)
        query = self.expand_node_returns(query)
        query = self.remove_apoc_calls(query)
        query = self.fix_property_names(query)
        query = self.clean_whitespace(query)
        
        return query
    
    def enforce_lowercase_contains(self, query: str) -> str:
        """
        Rule 1: Convert exact string matches to LOWER() + CONTAINS
        Example: WHERE s.name = 'Cambridge' 
              → WHERE LOWER(s.name) CONTAINS 'cambridge'
        """
        # Pattern: property = 'string'
        pattern = r"WHERE\s+(\w+)\.(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
        
        def replacement(match):
            var, prop, value = match.groups()
            # Only apply to name-like properties
            if prop.lower() in ['name', 'knownname', 'fullname']:
                self.rules_applied.append(f"lowercase_contains: {match.group(0)}")
                return f"WHERE LOWER({var}.{prop}) CONTAINS '{value.lower()}'"
            return match.group(0)
        
        return re.sub(pattern, replacement, query, flags=re.IGNORECASE)
    
    def expand_node_returns(self, query: str) -> str:
        """
        Rule 2: Expand node returns to specific properties
        Example: RETURN s → RETURN s.knownName, s.id
        """
        # Pattern: RETURN followed by just variable names
        pattern = r"RETURN\s+([a-z]\w*)\s*(?:,\s*([a-z]\w*)\s*)*$"
        
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match:
            variables = [v for v in match.groups() if v]
            # Expand based on common properties
            expanded = []
            for var in variables:
                # Heuristic: if variable is 's' or 'scholar', expand to scholar properties
                if var in ['s', 's1', 's2', 'scholar']:
                    expanded.append(f"{var}.knownName")
                elif var in ['p', 'p1', 'prize']:
                    expanded.append(f"{var}.category")
                    expanded.append(f"{var}.awardYear")
                else:
                    expanded.append(f"{var}.name")
            
            if expanded:
                self.rules_applied.append(f"expand_return: {match.group(0)}")
                new_return = f"RETURN {', '.join(expanded)}"
                return re.sub(pattern, new_return, query, flags=re.IGNORECASE)
        
        return query
    
    def remove_apoc_calls(self, query: str) -> str:
        """
        Rule 3: Remove APOC function calls (not supported in Kuzu)
        Example: apoc.path.expandConfig() → removed
        """
        if 'apoc.' in query.lower():
            self.rules_applied.append("remove_apoc")
            # Remove apoc function calls
            query = re.sub(
                r'apoc\.\w+\([^)]*\)',
                '',
                query,
                flags=re.IGNORECASE
            )
        return query
    
    def fix_property_names(self, query: str) -> str:
        """
        Rule 4: Fix common property name mistakes
        Based on actual schema from the project
        """
        corrections = {
            r'\.name\b(?=.*Scholar)': '.knownName',  # Scholar nodes use knownName
            r'\.amount\b': '.prizeAmount',           # Prize amount property
            r'\.year\b': '.awardYear',               # Award year property
        }
        
        for pattern, replacement in corrections.items():
            if re.search(pattern, query):
                self.rules_applied.append(f"fix_property: {pattern}")
                query = re.sub(pattern, replacement, query)
        
        return query
    
    def clean_whitespace(self, query: str) -> str:
        """Rule 5: Clean up whitespace and newlines"""
        # Remove extra newlines
        query = ' '.join(query.split())
        # Single spaces only
        query = re.sub(r'\s+', ' ', query)
        self.rules_applied.append("clean_whitespace")
        return query.strip()
    
    def get_applied_rules(self) -> list[str]:
        """Return list of rules that were applied"""
        return self.rules_applied
```

#### 3. Integration with Query Generation

```python
def generate_final_query(question, schema, conn):
    """Complete pipeline with all Task 1 enhancements"""
    
    # Step 1: Select examples
    selected_examples = exemplar_selector.select_top_k(question, k=3)
    examples_text = format_examples(selected_examples)
    
    # Step 2: Generate with refinement
    generator = QueryGenerator(conn, max_iterations=3)
    query, history = generator.generate_with_refinement(
        question=question,
        schema=schema,
        examples=examples_text
    )
    
    # Step 3: Post-process
    post_processor = CypherPostProcessor()
    final_query = post_processor.process(query)
    
    print(f"Rules applied: {post_processor.get_applied_rules()}")
    
    return final_query
```

#### 4. Advanced: Custom Rules Based on Error Patterns

Track common errors and add rules dynamically:

```python
class AdaptivePostProcessor(CypherPostProcessor):
    def __init__(self):
        super().__init__()
        self.error_patterns = []
    
    def learn_from_error(self, query: str, error: str):
        """Learn patterns from failed queries"""
        pattern = {
            'query_fragment': query[:100],
            'error': error,
            'timestamp': time.time()
        }
        self.error_patterns.append(pattern)
        
        # Analyze and add new rules
        if 'property does not exist' in error.lower():
            # Extract property name and suggest correction
            pass
```

### Testing Post-Processing

```python
test_queries = [
    {
        "input": "MATCH (s:Scholar) WHERE s.name = 'Einstein' RETURN s",
        "expected_fixes": ["lowercase_contains", "expand_return"]
    },
    {
        "input": "MATCH (s:Scholar) WHERE s.year > 2000 RETURN s.knownName",
        "expected_fixes": ["fix_property"]
    },
    {
        "input": "MATCH path = apoc.path.expandConfig(s) RETURN path",
        "expected_fixes": ["remove_apoc"]
    }
]

processor = CypherPostProcessor()

for test in test_queries:
    processed = processor.process(test['input'])
    print(f"\nOriginal: {test['input']}")
    print(f"Processed: {processed}")
    print(f"Rules applied: {processor.get_applied_rules()}")
```

---

## Integration: Complete Task 1 Pipeline

### Putting It All Together

```python
class EnhancedGraphRAG(dspy.Module):
    """GraphRAG with all Task 1 enhancements"""
    
    def __init__(self, conn, exemplars):
        self.conn = conn
        self.exemplar_selector = ExemplarSelector(exemplars)
        self.query_generator = QueryGenerator(conn, max_iterations=3)
        self.post_processor = CypherPostProcessor()
        
        self.prune = dspy.Predict(PruneSchema)
        self.generate_answer = dspy.ChainOfThought(AnswerQuestion)
        
        # Metrics tracking
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'refinement_iterations': [],
            'rules_applied': []
        }
    
    def forward(self, db_manager, question: str, input_schema: str):
        self.metrics['total_queries'] += 1
        
        # Step 1: Prune schema
        prune_result = self.prune(question=question, input_schema=input_schema)
        pruned_schema = prune_result.pruned_schema.model_dump()
        
        # Step 2: Select relevant examples
        selected_examples = self.exemplar_selector.select_top_k(question, k=3)
        examples_text = "\n\n".join([
            f"Q: {ex['question']}\nCypher: {ex['cypher']}"
            for ex in selected_examples
        ])
        
        # Step 3: Generate with refinement
        query, history = self.query_generator.generate_with_refinement(
            question=question,
            schema=str(pruned_schema),
            examples=examples_text
        )
        self.metrics['refinement_iterations'].append(len(history))
        
        # Step 4: Post-process
        final_query = self.post_processor.process(query)
        self.metrics['rules_applied'].extend(
            self.post_processor.get_applied_rules()
        )
        
        # Step 5: Execute and generate answer
        try:
            result = db_manager.conn.execute(final_query)
            context = [item for row in result for item in row]
            self.metrics['successful_queries'] += 1
        except Exception as e:
            print(f"Query execution failed: {e}")
            context = None
        
        if context is None:
            return {
                'question': question,
                'query': final_query,
                'answer': None,
                'error': 'Query execution failed'
            }
        
        # Step 6: Generate natural language answer
        answer = self.generate_answer(
            question=question,
            cypher_query=final_query,
            context=str(context)
        )
        
        return {
            'question': question,
            'query': final_query,
            'answer': answer,
            'context': context,
            'examples_used': [ex['question'] for ex in selected_examples],
            'iterations': len(history),
            'rules_applied': self.post_processor.get_applied_rules()
        }
    
    def get_metrics(self):
        """Return performance metrics"""
        return {
            'success_rate': self.metrics['successful_queries'] / self.metrics['total_queries'],
            'avg_iterations': sum(self.metrics['refinement_iterations']) / len(self.metrics['refinement_iterations']),
            'most_common_rules': Counter(self.metrics['rules_applied']).most_common(5)
        }
```

---

## Evaluation Criteria

### 1. Accuracy Metrics

Create a test set with ground truth:

```python
test_set = [
    {
        "question": "Which scholars won prizes in Physics?",
        "expected_cypher": "MATCH (s:Scholar)-[:WON]->(p:Prize) WHERE LOWER(p.category) = 'physics' RETURN s.knownName",
        "expected_results": ["Albert Einstein", "Marie Curie", ...]
    },
    # Add 20-30 test cases
]

def evaluate_accuracy(model, test_set):
    metrics = {
        'syntax_correct': 0,
        'semantic_correct': 0,
        'exact_match': 0
    }
    
    for test in test_set:
        result = model(
            db_manager=db_manager,
            question=test['question'],
            input_schema=schema
        )
        
        generated_query = result['query']
        
        # Check syntax
        is_valid, _ = validate_cypher(conn, generated_query)
        if is_valid:
            metrics['syntax_correct'] += 1
        
        # Check semantic correctness (do results match?)
        if result['context'] is not None:
            generated_set = set(result['context'])
            expected_set = set(test['expected_results'])
            
            if generated_set == expected_set:
                metrics['semantic_correct'] += 1
        
        # Check exact query match (optional, very strict)
        if generated_query.strip() == test['expected_cypher'].strip():
            metrics['exact_match'] += 1
    
    for key in metrics:
        metrics[key] = metrics[key] / len(test_set) * 100
    
    return metrics
```

### 2. Improvement Measurement

Compare before and after:

```python
# Baseline (no enhancements)
baseline_results = evaluate_accuracy(baseline_model, test_set)

# With Task 1 enhancements
enhanced_results = evaluate_accuracy(enhanced_model, test_set)

# Report improvements
print("=== Task 1 Improvements ===")
print(f"Syntax Accuracy: {baseline_results['syntax_correct']:.1f}% → {enhanced_results['syntax_correct']:.1f}% (+{enhanced_results['syntax_correct'] - baseline_results['syntax_correct']:.1f}%)")
print(f"Semantic Accuracy: {baseline_results['semantic_correct']:.1f}% → {enhanced_results['semantic_correct']:.1f}% (+{enhanced_results['semantic_correct'] - baseline_results['semantic_correct']:.1f}%)")
```

### 3. Component-Level Analysis

```python
# Track which enhancement contributes most
enhancements = [
    ('baseline', baseline_model),
    ('+ few-shot', model_with_few_shot),
    ('+ refinement', model_with_few_shot_and_refinement),
    ('+ post-processing', full_enhanced_model)
]

results_by_enhancement = {}
for name, model in enhancements:
    results_by_enhancement[name] = evaluate_accuracy(model, test_set)

# Plot improvement curve
import matplotlib.pyplot as plt

names = list(results_by_enhancement.keys())
syntax_scores = [r['syntax_correct'] for r in results_by_enhancement.values()]

plt.plot(names, syntax_scores, marker='o')
plt.xlabel('Enhancement Stage')
plt.ylabel('Syntax Accuracy (%)')
plt.title('Incremental Improvement from Task 1 Enhancements')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('task1_improvements.png')
```

---

## Deliverables for Task 1

### Code Files
1. `exemplar_selector.py` - Few-shot example selection
2. `query_refinement.py` - Self-refinement loop implementation
3. `post_processor.py` - Rule-based post-processing
4. `enhanced_graph_rag.py` - Integrated pipeline
5. `task1_evaluation.py` - Testing and metrics

### Documentation
1. Exemplar dataset (JSON/CSV)
2. Test set with ground truth queries
3. Evaluation results showing accuracy improvements
4. Comparison table (before/after each enhancement)

### For Report (Evaluation Section)
- Describe each enhancement and its motivation
- Present accuracy metrics (syntax correctness, semantic correctness)
- Show improvement over baseline
- Analyze which enhancement contributed most
- Include example queries showing refinement in action
- Present failure cases and discuss limitations

---

## Tips and Best Practices

### For Few-Shot Selection
- Include diverse query patterns in your exemplars
- Ensure examples are correct (validate them first)
- Consider category-based selection as fallback
- Cache embeddings to avoid recomputation

### For Self-Refinement
- Start with max 3 iterations (diminishing returns after that)
- Log all attempts for debugging
- Consider early stopping if error doesn't change
- Add timeout to prevent infinite loops

### For Post-Processing
- Test each rule independently first
- Make rules configurable (enable/disable)
- Be careful with regex - test edge cases
- Consider order of rule application

### Common Pitfalls
- Don't over-engineer - simple solutions often work best
- Validate on diverse test cases, not just easy ones
- Watch for LLM API rate limits during testing
- Keep track of costs (API calls add up)
- Test with the actual Kuzu database, not mock data
The accuracy improvements from Task 1 will make Task 2 more meaningful, as you'll be caching high-quality queries.

---

## Implementation and Connection to Task 2

The implementation of Task 1 is encapsulated within the `EnhancedGraphRAG` module, which integrates all the enhancements into a single pipeline. The `text_2_cypher` directory now contains all the helper modules for Task 1:

- **`exemplar_selector.py`**: Implements the `ExemplarSelector` class for dynamic few-shot exemplar selection using sentence embeddings.
- **`query_refinement.py`**: Implements the `QueryGenerator` class for the self-refinement loop, which includes query validation and repair.
- **`post_processor.py`**: Implements the `CypherPostProcessor` class for rule-based post-processing of the generated Cypher query.

The `EnhancedGraphRAG` module in `graph_rag.py` orchestrates the entire process:

1.  **Exemplar Selection**: The `ExemplarSelector` is used to select the most relevant examples for the input question.
2.  **Query Generation with Refinement**: The `QueryGenerator` takes the question, schema, and selected examples to generate a Cypher query, which is then validated and repaired if necessary.
3.  **Post-Processing**: The `CypherPostProcessor` cleans up and fixes the generated query.

### Connection to Task 2: Caching

The `EnhancedGraphRAG` module is connected to the `LRUDataManager` from Task 2 at the `run_query` level. This is how they are connected:

- **Cache Check**: Before initiating the query generation process, the `run_query` method first checks if the result for the given question is already in the cache using `cache_manager.get_data(question)`.
- **Cache Hit**: If a cached result is found, the entire query generation and execution process is skipped, and the cached query and results are returned directly. This significantly improves performance for repeated questions.
- **Cache Miss**: If the result is not in the cache, the `get_cypher_query` method is called to generate and refine the query. The query is then executed against the Kuzu database, and the result is stored in the cache using `cache_manager.set_data(question, {"query": query, "results": results})`. The question is used as the key, and a dictionary containing the query and its results is stored as the value.

This integration ensures that the performance benefits of caching from Task 2 are applied to the high-quality, refined queries generated by the Task 1 enhancements. By caching the final, validated query and its results, we avoid the computational overhead of query generation, refinement, and execution for subsequent identical requests.
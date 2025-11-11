# Graph RAG Workflow

This document describes the end-to-end process of the `graph_rag_workflow.py` script, a terminal-based application that leverages a Graph RAG (Retrieval-Augmented Generation) pipeline to answer natural language questions about a knowledge graph.

## Overview

The primary goal of the workflow is to accurately translate a user's question into a valid Cypher query, execute it against a Kuzu graph database, and generate a coherent, natural language answer from the results. The pipeline is designed to be robust and efficient, incorporating advanced features like query self-refinement and intelligent caching.

## End-to-End Workflow

The script operates as an interactive chat session. When the user submits a question, the following sequence is triggered:

1.  **Schema Pruning**: The full graph schema is dynamically pruned by an LLM to create a smaller, contextually relevant schema containing only the nodes, relationships, and properties relevant to the user's question.

2.  **Cache Check**: A unique key is generated from the user's question and the pruned schema. The system checks an in-memory LRU Cache to see if a final answer for this key already exists.
    *   **Cache Hit**: If an answer is found, it is returned directly to the user, and the process stops here. This provides a near-instantaneous response.
    *   **Cache Miss**: If no answer is found, the full Text2Cypher pipeline is executed.

3.  **Text2Cypher Execution**: This multi-stage component generates a valid Cypher query. (See detailed breakdown below).

4.  **Database Query**: The final, validated Cypher query is executed against the Kuzu database.

5.  **Answer Generation**: The results from the database are passed as context to an LLM, which generates a final, human-readable answer.

6.  **Cache Update**: This newly generated final answer is stored in the LRU cache with the key from step 2, making future requests for the same question much faster.

## Component Deep Dive

### The Text2Cypher Component

This is the core component responsible for converting the user's question into a valid Cypher query. It operates in several stages:

#### 1. Dynamic Exemplar Selection
To give the LLM better context, the system selects relevant examples from a predefined list of question-query pairs (exemplars).
-   **How it works**: It uses a TF-IDF vectorizer to convert the user's question and all exemplar questions into numerical representations. It then calculates the Cosine Similarity between the user's question and each exemplar to find the top 2 most semantically similar examples.
-   **Purpose**: This provides the LLM with highly relevant, in-context examples, dramatically improving the accuracy of the generated query.

#### 2. Query Generation & Self-Refinement
This is an iterative loop that ensures the generated query is valid.
-   **Generation**: The LLM attempts to generate a Cypher query using the user's question, the pruned schema, and the dynamically selected exemplars.
-   **Validation**: The generated query is **not** executed immediately. Instead, the system runs an `EXPLAIN` command against the database. This is a dry run that checks for syntax errors, schema violations, and other issues without incurring the cost of a full execution.
-   **Repair**: If the `EXPLAIN` command fails, the original query, the error message, and the initial context are fed back into a specialized "repair" LLM prompt. This prompt guides the LLM to fix its own mistake. The loop repeats until a valid query is generated or a maximum number of iterations is reached.

#### 3. Post-Processing
Once a valid query is generated, a series of rule-based processors clean and standardize it. This includes:
-   Enforcing lowercase `CONTAINS` for string comparisons.
-   Correcting common property name mistakes (e.g., ensuring `Scholar` nodes use `knownName`).
-   Removing extra whitespace.

### The Caching Mechanism (`cache_method`)

The caching layer is designed to maximize performance and minimize redundant computations.

-   **Strategy**: It caches the **final natural language answer**, which is the most valuable and expensive artifact to produce.
-   **Key Generation**: The cache key is a SHA-256 hash of a string composed of the user's full question and the JSON representation of the pruned schema. Using the pruned schema in the key ensures that if two different questions result in the same query but had different schema contexts, they are treated as unique entries.
-   **Logic**:
    -   On a **Cache Hit**, the entire Text2Cypher pipeline, database query, and answer generation steps are skipped, providing a significant speedup.
    -   On a **Cache Miss**, the full pipeline runs, and the final answer is placed into the cache before being sent to the user.
-   **Implementation**: It uses an in-memory **LRU (Least Recently Used)** cache, which automatically evicts the least recently used items when the cache reaches its size limit.

## How to Run the Workflow

The script runs as an interactive command-line application.

```bash
python graph_rag_workflow.py
```

The application will start, and you can begin asking questions at the `>` prompt.

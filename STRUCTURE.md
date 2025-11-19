# Repository Structure

This document outlines the structure of the GraphRAG project repository. The goal of this project is to build an advanced Retrieval-Augmented Generation (RAG) system that uses a Knowledge Graph to answer user questions. It enhances a standard Text-to-Cypher pipeline with features like dynamic example selection, query self-refinement, and caching.

## Core Components

### `text_2_cypher/`

This module contains all components related to enhancing the Text-to-Cypher generation process, as required by Task 1 of the project.

-   `exemplar_selector.py`: Implements the `ExemplarSelector` class, which dynamically selects relevant few-shot examples from a predefined list based on the user's question. This helps improve the quality of the generated Cypher query by providing more relevant context to the LLM.
-   `query_refinement.py`: Implements the `QueryGenerator` class. This component is responsible for the self-refinement loop. It generates a Cypher query, validates it against the database using `EXPLAIN`, and if validation fails, it attempts to repair the query based on the error message.
-   `post_processor.py`: Implements the `CypherPostProcessor` class, which applies a series of rule-based transformations to the final, valid Cypher query to clean it up and enforce best practices (e.g., using `LOWER()` and `CONTAINS` for string matching).

### `cache_method/`

This module provides a caching layer to improve system performance, as required by Task 2 of the project.

-   `data_manager.py`: Defines a base `DataManager` class with a simple `LRUCache`.
-   `cache.py`: Implements `LRUDataManager`, which extends the base manager. It is used in the advanced workflow to cache successfully generated Cypher queries, using a key derived from the user's question and the pruned graph schema.

## Data and Setup

-   `data/`: Contains the raw `nobel.json` dataset.
-   `nobel.kuzu`: The Kuzu graph database file.
-   `convert_nobel_json.py`: A script to preprocess the raw JSON data.
-   `create_nobel_api_graph.py`: A script to take the processed data and build the Kuzu graph database.
-   `docker-compose.yml`: Defines services, likely for the Kuzu database if it were to be run in a container.

## Workflows

The project includes two Marimo notebooks that demonstrate the RAG pipeline.

-   `demo_workflow.py`: A basic demonstration of a GraphRAG pipeline. It shows the fundamental steps: schema pruning, Text-to-Cypher generation, query execution, and final answer generation. It does **not** use the advanced components from the `text_2_cypher` or `cache_method` modules.

-   `advanced_demo_workflow.py`: The main workflow that integrates all the advanced features developed in the project into a single, robust pipeline.

### `advanced_demo_workflow.py`: Detailed Breakdown

This notebook demonstrates the complete, enhanced GraphRAG pipeline. It's designed to be an interactive application where a user can ask a question and see the full process of generating an answer.

**What it does and what's supposed to be happening:**

The workflow executes a multi-stage pipeline to answer a user's question:

1.  **Initialization**: It starts by connecting to the Kuzu database (`nobel.kuzu`) and configuring the LLM (e.g., Gemini 2.5 Flash via Vertex AI).

2.  **Component Setup**: It initializes all the custom modules: `ExemplarSelector`, `QueryGenerator`, `CypherPostProcessor`, and `LRUDataManager`.

3.  **Schema Pruning**: When a user enters a question, the workflow first prunes the full graph schema down to a smaller, relevant subset. This helps the LLM focus on only the parts of the graph needed to answer the question.

4.  **Cache Lookup**: It then checks for a cached result. A unique key is generated from the user's question and the pruned schema. The `LRUDataManager` is queried with this key to see if a valid Cypher query has already been generated and stored.

5.  **Query Generation (on Cache Miss)**: If no query is found in the cache, the pipeline proceeds to generate one:
    *   **Dynamic Exemplar Selection**: The `ExemplarSelector` chooses the 2 most similar question-query pairs from a predefined list to serve as few-shot examples for the LLM.
    *   **Generate & Refine**: The `QueryGenerator` is called. It makes an initial attempt to generate a Cypher query. It then enters a self-refinement loop where it validates the query's syntax with the database. If the query is invalid, it uses the database error to prompt the LLM to repair it. This loop runs for a maximum of 3 iterations.
    *   **Post-Processing**: The syntactically valid query from the refinement step is passed to the `CypherPostProcessor`. This applies several rule-based cleanups, such as enforcing lowercase string comparisons and expanding `RETURN` statements.

6.  **Cache Update**: The newly generated, refined, and post-processed query is stored in the `LRUDataManager` with its corresponding key.

7.  **Execution and Final Answer**: The final, polished Cypher query is executed against the Kuzu database. The results from the database are then passed as context to a final LLM call, which generates a natural language answer to the user's original question. The notebook displays the cache status, the final query, any applied post-processing rules, and the final answer.

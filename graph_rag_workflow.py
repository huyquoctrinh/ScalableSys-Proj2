import os
import json
import kuzu
import dspy
import datetime
import time
import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from text_2_cypher import (
    ExemplarSelector,
    QueryGenerator,
    CypherPostProcessor,
)
from cache_method import LRUDataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('graph_rag_detailed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Pydantic Models and DSPy Signatures ===
class Query(BaseModel):
    query: str = Field(description="Valid Cypher query with no newlines")

class Property(BaseModel):
    name: str
    type: str = Field(description="Data type of the property")

class Node(BaseModel):
    label: str
    properties: list[Property] | None

class Edge(BaseModel):
    label: str = Field(description="Relationship label")
    from_: str = Field(alias="from", description="Source node label")
    to: str = Field(alias="to", description="Target node label")
    properties: list[Property] | None

class GraphSchema(BaseModel):
    nodes: list[Node]
    edges: list[Edge]

class PruneSchema(dspy.Signature):
    """
    Understand the given labelled property graph schema and the given user question. Your task
    is to return ONLY the subset of the schema (node labels, edge labels and properties) that is
    relevant to the question.
    """
    question: str = dspy.InputField()
    input_schema: str = dspy.InputField()
    pruned_schema: GraphSchema = dspy.OutputField()

class Text2Cypher(dspy.Signature):
    """
    Translate the question into a valid Cypher query that respects the graph schema.

    <SYNTAX>
    - When matching on Scholar names, ALWAYS match on the `knownName` property
    - For countries, cities, continents and institutions, you can match on the `name` property
    - Use short, concise alphanumeric strings as names of variable bindings (e.g., `a1`, `r1`, etc.)
    - Always strive to respect the relationship direction (FROM/TO) using the schema information.
    - When comparing string properties, ALWAYS do the following:
      - Lowercase the property values before comparison
      - Use the WHERE clause
      - Use the CONTAINS operator to check for presence of one substring in the other
    - DO NOT use APOC as the database does not support it.
    </SYNTAX>

    <RETURN_RESULTS>
    - If the result is an integer, return it as an integer (not a string).
    - When returning results, return property values rather than the entire node or relationship.
    - Do not attempt to coerce data types to number formats (e.g., integer, float) in your results.
    - NO Cypher keywords should be returned by your query.
    </RETURN_RESULTS>
    """
    question: str = dspy.InputField()
    input_schema: str = dspy.InputField()
    examples: str = dspy.InputField(desc="Few-shot examples of question-query pairs.")
    query: Query = dspy.OutputField()

class AnswerQuestion(dspy.Signature):
    """
    - Use the provided question, the generated Cypher query and the context to answer the question.
    - If the context is empty, state that you don't have enough information to answer the question.
    """
    question: str = dspy.InputField()
    cypher_query: str = dspy.InputField()
    context: str = dspy.InputField()
    response: str = dspy.OutputField()

# === Helper Functions ===
def get_schema_dict(conn: kuzu.Connection) -> dict[str, list[dict]]:
    response = conn.execute("CALL SHOW_TABLES() WHERE type = 'NODE' RETURN *;")
    nodes = [row[1] for row in response]
    response = conn.execute("CALL SHOW_TABLES() WHERE type = 'REL' RETURN *;")
    rel_tables = [row[1] for row in response]
    relationships = []
    for tbl_name in rel_tables:
        response = conn.execute(f"CALL SHOW_CONNECTION('{tbl_name}') RETURN *;")
        for row in response:
            relationships.append({"name": tbl_name, "from": row[0], "to": row[1]})
    schema = {"nodes": [], "edges": []}
    for node in nodes:
        node_schema = {"label": node, "properties": []}
        node_properties = conn.execute(f"CALL TABLE_INFO('{node}') RETURN *;")
        for row in node_properties:
            node_schema["properties"].append({"name": row[1], "type": row[2]})
        schema["nodes"].append(node_schema)
    for rel in relationships:
        edge = {
            "label": rel["name"],
            "from": rel["from"],
            "to": rel["to"],
            "properties": [],
        }
        rel_properties = conn.execute(f"CALL TABLE_INFO('{rel['name']}') RETURN *;")
        for row in rel_properties:
            edge["properties"].append({"name": row[1], "type": row[2]})
        schema["edges"].append(edge)
    return schema

def setup_llm():
    """
    Sets up the language model from either Vertex AI or OpenRouter
    based on available environment variables.
    """
    load_dotenv()

    # Check for Vertex AI first
    vertex_project_id = os.environ.get("VERTEX_AI_PROJECT_ID")
    vertex_location = os.environ.get("VERTEX_AI_LOCATION")
    if vertex_project_id and vertex_location:
        print("Using Vertex AI...")
        lm = dspy.LM(model="vertex_ai/gemini-2.5-flash", project=vertex_project_id, location=vertex_location)
        dspy.configure(lm=lm)
        return lm

    # If Vertex AI is not found, check for OpenRouter
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_api_key:
        print("Using OpenRouter...")
        openrouter_model = "google/gemini-flash-1.5"
        lm = dspy.LM(
            model="openrouter/google/gemini-2.0-flash-001",
            api_base="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        dspy.configure(lm=lm)
        return lm

    # If neither is configured
    print("Error: No LLM provider configured.")
    print("Please set either VERTEX_AI_PROJECT_ID and VERTEX_AI_LOCATION, or OPENROUTER_API_KEY in your .env file.")
    return None

class BenchmarkStats:
    """Tracks performance statistics for cache benchmarking."""
    def __init__(self):
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.hit_times: List[float] = []
        self.miss_times: List[float] = []
        self.total_time_saved = 0.0
    
    def record_hit(self, elapsed_time: float):
        self.cache_hits += 1
        self.total_queries += 1
        self.hit_times.append(elapsed_time)
    
    def record_miss(self, elapsed_time: float):
        self.cache_misses += 1
        self.total_queries += 1
        self.miss_times.append(elapsed_time)
        # Estimate time saved based on average miss time
        if len(self.miss_times) > 0:
            avg_miss_time = sum(self.miss_times) / len(self.miss_times)
            self.total_time_saved = self.cache_hits * avg_miss_time
    
    def get_report(self) -> str:
        """Generate a formatted benchmark report."""
        if self.total_queries == 0:
            return "No queries processed yet."
        
        hit_rate = (self.cache_hits / self.total_queries) * 100
        avg_hit_time = sum(self.hit_times) / len(self.hit_times) if self.hit_times else 0
        avg_miss_time = sum(self.miss_times) / len(self.miss_times) if self.miss_times else 0
        
        report = [
            "\n" + "="*60,
            "📊 CACHE PERFORMANCE BENCHMARK",
            "="*60,
            f"Total Queries:        {self.total_queries}",
            f"Cache Hits:           {self.cache_hits} ({hit_rate:.1f}%)",
            f"Cache Misses:         {self.cache_misses} ({100-hit_rate:.1f}%)",
            "",
            f"⚡ Avg Hit Time:      {avg_hit_time:.3f}s",
            f"🐌 Avg Miss Time:     {avg_miss_time:.3f}s",
            f"🚀 Speedup (cached):  {avg_miss_time/avg_hit_time:.1f}x faster" if avg_hit_time > 0 else "",
            "",
            f"⏱️  Total Time Saved:  {self.total_time_saved:.2f}s",
            f"💰 Estimated Cost Saved: ${self.cache_hits * 0.002:.4f}",
            "="*60,
        ]
        return "\n".join(filter(None, report))

def process_question(
    question: str,
    conn: kuzu.Connection,
    get_schema_dict_func,
    prune_module,
    lru_cache_manager,
    exemplar_selector,
    query_generator,
    post_processor,
    answer_generator_module,
    benchmark_stats: BenchmarkStats = None,
) -> list[str]:
    """Handles the processing of a single user question with efficient caching of the final answer."""
    start_time = time.time()
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"❓ QUESTION: {question}")
    output.append(f"{'='*60}\n")

    # === 1. Prune Schema and Generate Cache Keys ===
    input_schema = get_schema_dict_func(conn)
    pruned_schema_result = prune_module(question=question, input_schema=json.dumps(input_schema, indent=2))
    pruned_schema = pruned_schema_result.pruned_schema.model_dump()
    schema_str = json.dumps(pruned_schema, sort_keys=True)
    base_cache_key = f"{question}|{schema_str}"
    
    answer_cache_key = f"answer|{base_cache_key}"
    hashed_answer_key = lru_cache_manager._hash(answer_cache_key)

    # === 2. Check Cache for Final Answer ===
    cached_answer = lru_cache_manager.get_data(hashed_answer_key)
    if cached_answer:
        elapsed_time = time.time() - start_time
        
        # Log cache hit
        logger.info("="*60)
        logger.info("CACHE HIT - Skipping database query")
        logger.info("="*60)
        logger.info(f"Question: {question}")
        logger.info(f"Cache key: {hashed_key[:16]}...")
        logger.info(f"Response time: {elapsed_time:.3f}s")
        logger.info(f"Cached answer: {cached_answer}")
        logger.info(f"Cache size: {len(lru_cache_manager.cache)}/{lru_cache_manager.cache.maxsize}")
        logger.info("="*60 + "\n")
        
        output.append("✅ Cache Status: HIT")
        output.append(f"⚡ Response Time: {elapsed_time:.3f}s")
        output.append(f"📦 Cache Size: {len(lru_cache_manager.cache)}/{lru_cache_manager.cache.maxsize}")
        output.append(f"\n💡 ANSWER:\n{cached_answer}")
        
        if benchmark_stats:
            benchmark_stats.record_hit(elapsed_time)
        
        return output

    # === 3. Cache Miss: Run Full Pipeline ===
    output.append("❌ Cache Status: MISS")
    
    output.append("Answer Cache Status: MISS")

    # === 3. Check Cache for Cypher Query ===
    query_cache_key = f"query|{base_cache_key}"
    hashed_query_key = lru_cache_manager._hash(query_cache_key)
    cached_query_data = lru_cache_manager.get_data(hashed_query_key)

    query_history = []
    applied_rules = []

    if cached_query_data:
        output.append("Cypher Query Cache Status: HIT")
        final_query = cached_query_data["query"]
        query_history = cached_query_data.get("history", [])
        applied_rules = cached_query_data.get("rules", [])
    else:
        output.append("Cypher Query Cache Status: MISS")
        # --- a. Generate and Process Query ---
        top_k_exemplars = exemplar_selector.select_top_k(question, k=2)
        generated_query, query_history = query_generator.generate_with_refinement(
            question=question, schema=json.dumps(pruned_schema, indent=2), examples=str(top_k_exemplars)
        )
        final_query = post_processor.process(generated_query)
        applied_rules = post_processor.get_applied_rules()

        # Store the generated query and metadata in the cache
        query_to_cache = {
            "query": final_query,
            "history": query_history,
            "rules": applied_rules,
        }
        lru_cache_manager.set_data(hashed_query_key, query_to_cache)

    output.append(f"\nFinal Cypher Query:\n{final_query}")
    if applied_rules:
        output.append(f"Post-processing Rules Applied: {applied_rules}")
    if query_history:
        output.append("Query Generation History:")
        for i, q in enumerate(query_history):
            output.append(f"  - Attempt {i+1}: {q}")

    # --- b. Execute Query and Log Database Retrieval ---
    output.append("\n--- Running Query and Generating Answer ---")
    
    # Log query execution
    logger.info("="*60)
    logger.info("DATABASE QUERY EXECUTION")
    logger.info("="*60)
    logger.info(f"Question: {question}")
    logger.info(f"Cypher Query: {final_query}")
    
    db_start_time = time.time()
    try:
        result = conn.execute(final_query)
        db_execution_time = time.time() - db_start_time
        
        # Get results as dataframe for better logging
        df = result.get_as_df()
        context = [item for row in df.values for item in row]
        
        # Log retrieval details
        logger.info(f"✓ Query executed successfully in {db_execution_time:.3f}s")
        logger.info(f"Number of rows retrieved: {len(df)}")
        logger.info(f"Number of values: {len(context)}")
        logger.info(f"Column names: {list(df.columns)}")
        
        # Log sample of results (first 5 rows)
        logger.info("Sample results (first 5 rows):")
        for idx, row in enumerate(df.head(5).values):
            logger.info(f"  Row {idx+1}: {row}")
        
        if len(df) > 5:
            logger.info(f"  ... and {len(df) - 5} more rows")
        
        # Log full context
        logger.info(f"Full context for answer generation: {context}")
        
        output.append(f"\n📊 Database Retrieval Results:")
        output.append(f"   • Rows retrieved: {len(df)}")
        output.append(f"   • Execution time: {db_execution_time:.3f}s")
        output.append(f"   • Columns: {', '.join(df.columns)}")
        output.append(f"\nQuery Result:\n{context}")
        
    except RuntimeError as e:
        db_execution_time = time.time() - db_start_time
        context = None
        error_msg = str(e)
        
        # Log error details
        logger.error(f"✗ Query execution failed after {db_execution_time:.3f}s")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {error_msg}")
        logger.error(f"Failed query: {final_query}")
        
        output.append(f"\n❌ Error running query: {error_msg}")
        output.append(f"   • Execution time: {db_execution_time:.3f}s")

    # --- c. Generate Final Answer and Update Cache ---
    if context is None:
        output.append("\n❌ Could not generate an answer due to a query error.")
        logger.warning("No context available for answer generation")
    else:
        # Log answer generation
        logger.info("Generating natural language answer from context...")
        answer_start_time = time.time()
        
        answer_obj = answer_generator_module(
            question=question, cypher_query=final_query, context=str(context)
        )
        final_answer = answer_obj.response
        answer_gen_time = time.time() - answer_start_time
        
        logger.info(f"✓ Answer generated in {answer_gen_time:.3f}s")
        logger.info(f"Answer length: {len(final_answer)} characters")
        logger.info(f"Final Answer: {final_answer}")
        
        # Store the final answer in the cache
        lru_cache_manager.set_data(hashed_key, final_answer)
        logger.info(f"✓ Answer cached with key: {hashed_key[:16]}...")
        
        elapsed_time = time.time() - start_time
        
        # Log performance breakdown
        logger.info("="*60)
        logger.info("PERFORMANCE BREAKDOWN")
        logger.info("="*60)
        logger.info(f"Database query time: {db_execution_time:.3f}s")
        logger.info(f"Answer generation time: {answer_gen_time:.3f}s")
        logger.info(f"Total processing time: {elapsed_time:.3f}s")
        logger.info(f"Cache size: {len(lru_cache_manager.cache)}/{lru_cache_manager.cache.maxsize}")
        logger.info("="*60 + "\n")
        
        output.append(f"\n⏱️  Total Processing Time: {elapsed_time:.3f}s")
        output.append(f"   • DB Query: {db_execution_time:.3f}s")
        output.append(f"   • Answer Gen: {answer_gen_time:.3f}s")
        output.append(f"📦 Cache Size: {len(lru_cache_manager.cache)}/{lru_cache_manager.cache.maxsize}")
        output.append(f"\n💡 ANSWER:\n{final_answer}")
        
        if benchmark_stats:
            benchmark_stats.record_miss(elapsed_time)
    
    return output

def main():
    """Initializes components and runs the main chat loop with logging and benchmarking."""
    print("="*60)
    print("🚀 Graph RAG with LRU Cache - Performance Benchmark")
    print("="*60)
    print("Type 'exit', 'quit' to end, or 'stats' to see benchmark report.")
    print("="*60)

    # === 1. One-time Configuration and Setup ===
    lm = setup_llm()
    if not lm:
        return

    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name, read_only=True)
    conn = kuzu.Connection(db)

    # === 2. One-time Component Initialization ===
    # Load exemplars from JSON file
    try:
        with open('exemplars.json', 'r') as f:
            exemplars = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading exemplars.json: {e}")
        print("Please ensure exemplars.json exists and is valid. Exiting.")
        return
    exemplar_selector = ExemplarSelector(exemplars=exemplars)
    post_processor = CypherPostProcessor()
    lru_cache_manager = LRUDataManager(cache_size=128)
    
    text2cypher_predictor = dspy.ChainOfThought(Text2Cypher)
    query_generator = QueryGenerator(conn=conn, text2cypher_predictor=text2cypher_predictor)

    prune_module = dspy.ChainOfThought(PruneSchema)
    answer_generator_module = dspy.ChainOfThought(AnswerQuestion)
    
    # Initialize benchmark statistics
    benchmark_stats = BenchmarkStats()

    # === 3. Main Chat Loop with Logging and Benchmarking ===
    log_filename = "chat_log.txt"
    print(f"\n📝 Logging chat to {log_filename}\n")

    with open(log_filename, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n--- Session started at {datetime.datetime.now().isoformat()} ---\n")
        
        while True:
            try:
                user_question = input("\n> ")
                if not user_question.strip():
                    continue
                
                log_file.write(f"\n> {user_question}\n")

                # Check for special commands
                if user_question.strip().lower() in ["exit", "quit"]:
                    # Show final benchmark report before exiting
                    final_report = benchmark_stats.get_report()
                    print(final_report)
                    log_file.write(f"\n{final_report}\n")
                    print("\n👋 Exiting chat session.")
                    log_file.write(f"--- Session ended at {datetime.datetime.now().isoformat()} ---\n")
                    break
                
                if user_question.strip().lower() == "stats":
                    # Show current benchmark statistics
                    stats_report = benchmark_stats.get_report()
                    print(stats_report)
                    log_file.write(f"\n{stats_report}\n")
                    continue

                output_lines = process_question(
                    question=user_question,
                    conn=conn,
                    get_schema_dict_func=get_schema_dict,
                    prune_module=prune_module,
                    lru_cache_manager=lru_cache_manager,
                    exemplar_selector=exemplar_selector,
                    query_generator=query_generator,
                    post_processor=post_processor,
                    answer_generator_module=answer_generator_module,
                    benchmark_stats=benchmark_stats,
                )

                for line in output_lines:
                    print(line)
                    log_file.write(f"{line}\n")

            except (KeyboardInterrupt, EOFError):
                # Show final benchmark report before exiting
                final_report = benchmark_stats.get_report()
                print(f"\n{final_report}")
                log_file.write(f"\n{final_report}\n")
                print("\n👋 Exiting chat session.")
                log_file.write(f"--- Session ended abruptly at {datetime.datetime.now().isoformat()} ---\n")
                break
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                print(error_message)
                log_file.write(f"{error_message}\n")
                print("Please try again.")

if __name__ == "__main__":
    main()

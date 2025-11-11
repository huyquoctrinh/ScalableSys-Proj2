import os
import json
import kuzu
import dspy
import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from text_2_cypher import (
    ExemplarSelector,
    QueryGenerator,
    CypherPostProcessor,
)
from cache_method import LRUDataManager

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
        lm = dspy.OpenRouter(model=openrouter_model, api_key=openrouter_api_key)
        dspy.configure(lm=lm)
        return lm

    # If neither is configured
    print("Error: No LLM provider configured.")
    print("Please set either VERTEX_AI_PROJECT_ID and VERTEX_AI_LOCATION, or OPENROUTER_API_KEY in your .env file.")
    return None

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
) -> list[str]:
    """Handles the processing of a single user question with two-level caching: first for the final answer, then for the generated Cypher query."""
    output = []
    output.append(f"\nProcessing question: {question}\n")

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
        output.append("Answer Cache Status: HIT")
        output.append(f"\nFinal Answer:\n> {cached_answer}")
        return output
    
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

    # --- b. Execute Query ---
    output.append("\n--- Running Query and Generating Answer ---")
    try:
        result = conn.execute(final_query)
        context = [item for row in result.get_as_df().values for item in row]
        output.append(f"\nQuery Result:\n{context}")
    except RuntimeError as e:
        context = None
        output.append(f"\nError running query: {e}")

    # --- c. Generate Final Answer and Update Cache ---
    if context is None:
        output.append("\nCould not generate an answer due to a query error.")
    else:
        answer_obj = answer_generator_module(
            question=question, cypher_query=final_query, context=str(context)
        )
        final_answer = answer_obj.response
        output.append(f"\nFinal Answer:\n> {final_answer}")
        
        # Store the final answer in the cache
        lru_cache_manager.set_data(hashed_answer_key, final_answer)
    
    return output

def main():
    """Initializes components and runs the main chat loop with logging."""
    print("Starting Graph RAG chat session. Type 'exit' or 'quit' to end.")

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

    # === 3. Main Chat Loop with Logging ===
    log_filename = "chat_log.txt"
    print(f"Logging chat to {log_filename}")

    with open(log_filename, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n--- Session started at {datetime.datetime.now().isoformat()} ---\n")
        
        while True:
            try:
                user_question = input("\n> ")
                if not user_question.strip():
                    continue
                
                log_file.write(f"\n> {user_question}\n")

                if user_question.strip().lower() in ["exit", "quit"]:
                    print("Exiting chat session.")
                    log_file.write(f"--- Session ended at {datetime.datetime.now().isoformat()} ---\n")
                    break

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
                )

                for line in output_lines:
                    print(line)
                    log_file.write(f"{line}\n")

            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat session.")
                log_file.write(f"--- Session ended abruptly at {datetime.datetime.now().isoformat()} ---\n")
                break
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                print(error_message)
                log_file.write(f"{error_message}\n")
                print("Please try again.")

if __name__ == "__main__":
    main()

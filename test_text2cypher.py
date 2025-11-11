
import os
import json
import kuzu
import dspy
from dotenv import load_dotenv
import pandas as pd

# Import components from the main workflow
from graph_rag_workflow import (
    setup_llm,
    get_schema_dict,
    PruneSchema,
    Text2Cypher,
    AnswerQuestion,
    Query,
    GraphSchema,
    Node,
    Edge,
    Property
)
from text_2_cypher import (
    ExemplarSelector,
    QueryGenerator,
    CypherPostProcessor,
)

def run_query_and_get_results(conn: kuzu.Connection, query: str) -> set:
    """Executes a query and returns the results as a set of tuples for comparison."""
    try:
        result = conn.execute(query)
        # Convert result to a DataFrame, then to a list of tuples, then to a set
        df = result.get_as_df()
        # Convert all data to string to handle type differences (e.g., 1999 vs '1999')
        df = df.astype(str)
        return set(map(tuple, df.to_records(index=False)))
    except Exception as e:
        print(f"  \033[91mError executing query:\033[0m {e}")
        return set()


def test_text2cypher_pipeline():
    """
    Tests the Text2Cypher pipeline by comparing generated queries and their
    execution results against a set of ground-truth exemplars.
    """
    print("--- Starting Text2Cypher Pipeline Test ---")

    # === 1. One-time Configuration and Setup ===
    lm = setup_llm()
    if not lm:
        return

    db_name = "nobel.kuzu"
    try:
        db = kuzu.Database(db_name, read_only=True)
        conn = kuzu.Connection(db)
    except Exception as e:
        print(f"Failed to connect to KuzuDB: {e}")
        return

    # === 2. Load Exemplars (Separate Train and Test) ===
    try:
        with open('train_exemplars.json', 'r') as f:
            train_exemplars = json.load(f)
        with open('test_exemplars.json', 'r') as f:
            test_exemplars = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading exemplar files: {e}")
        return

    # === 3. Initialize Modules ===
    prune_module = dspy.ChainOfThought(PruneSchema)
    text2cypher_predictor = dspy.ChainOfThought(Text2Cypher)
    query_generator = QueryGenerator(conn=conn, text2cypher_predictor=text2cypher_predictor)
    post_processor = CypherPostProcessor()
    # ExemplarSelector is now initialized with only the training set
    exemplar_selector = ExemplarSelector(exemplars=train_exemplars)

    total_tests = len(test_exemplars)
    passed_tests = 0

    # === 4. Loop Through Test Exemplars and Test ===
    for i, exemplar in enumerate(test_exemplars):
        question = exemplar["question"]
        expected_query = exemplar["query"]
        
        print(f"\n--- Test {i+1}/{total_tests} ---")
        print(f"\033[1mQuestion:\033[0m {question}")

        # --- a. Generate Query using the pipeline ---
        input_schema = get_schema_dict(conn)
        pruned_schema_result = prune_module(question=question, input_schema=json.dumps(input_schema, indent=2))
        pruned_schema = pruned_schema_result.pruned_schema.model_dump()
        
        # Select examples from the training set to help guide the model
        top_k_exemplars = exemplar_selector.select_top_k(question, k=2)
        
        generated_query_obj, _ = query_generator.generate_with_refinement(
            question=question, schema=json.dumps(pruned_schema, indent=2), examples=str(top_k_exemplars)
        )
        generated_query = post_processor.process(generated_query_obj)

        print(f"\033[94mExpected Query:\033[0m {expected_query}")
        print(f"\033[96mGenerated Query:\033[0m {generated_query}")

        # --- b. Execute queries and compare results ---
        expected_results = run_query_and_get_results(conn, expected_query)
        generated_results = run_query_and_get_results(conn, generated_query)

        if expected_results == generated_results:
            print("\033[92m[PASSED] Query results match.\033[0m")
            passed_tests += 1
        else:
            print("\033[91m[FAILED] Query results DO NOT match.\033[0m")
            print(f"  Expected Results: {expected_results}")
            print(f"  Generated Results: {generated_results}")

    # === 5. Report Final Results ===
    print(f"\n--- Test Summary ---")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.2f}%")
    print("--------------------")


if __name__ == "__main__":
    test_text2cypher_pipeline()

import marimo
import json

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Advanced Graph RAG Workflow
    This notebook demonstrates an advanced Graph RAG workflow that integrates the full `text_2_cypher` and `cache_method` components.

    **Enhancements:**
    1.  **LRU Cache**: Caches generated Cypher queries to avoid re-computation for repeated questions.
    2.  **Dynamic Exemplar Selection**: Selects relevant few-shot examples based on the user's question to improve prompt quality.
    3.  **Self-Refinement Loop**: A `QueryGenerator` attempts to generate a query, validates it with the database, and repairs it upon failure.
    4.  **Post-Processing**: A rule-based processor cleans and standardizes the final, valid Cypher query.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""First, let's set up the database connection and LLM configuration.""")
    return


@app.cell
def _(kuzu):
    db_name = "nobel.kuzu"
    db = kuzu.Database(db_name, read_only=True)
    conn = kuzu.Connection(db)
    return conn, db_name


@app.cell
def _(BAMLAdapter, dspy, load_dotenv, os):
    load_dotenv()
    
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    
    # Using OpenRouter with Gemini 2.0 Flash for cost-efficiency
    lm = dspy.LM(
        model="openrouter/google/gemini-2.0-flash-001",
        api_base="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    dspy.configure(lm=lm, adapter=BAMLAdapter())
    return (lm, OPENROUTER_API_KEY)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Next, we import all the custom components from our `text_2_cypher` and `cache_method` modules.""")
    return


@app.cell
def _(
    CypherPostProcessor,
    ExemplarSelector,
    LRUDataManager,
    QueryGenerator,
    Text2Cypher,
    conn,
):
    # Define exemplars for the selector
    exemplars = [
        {
            "question": "Who were the mentors of Marie Curie?",
            "query": "MATCH (s1:Scholar {knownName: 'Marie Curie'})<-[:MENTORED]-(s2:Scholar) RETURN s2.knownName",
        },
        {
            "question": "Which prizes did Albert Einstein win?",
            "query": "MATCH (s:Scholar {knownName: 'Albert Einstein'})-[:AWARDED_PRIZE]->(p:Prize) RETURN p.category, p.awardYear",
        },
        {
            "question": "How many scholars are from Germany?",
            "query": "MATCH (s:Scholar)-[:BORN_IN]->(c:Country {name: 'Germany'}) RETURN count(s)",
        },
        {
            "question": "List scholars affiliated with University of Cambridge.",
            "query": "MATCH (s:Scholar)-[:AFFILIATED_WITH]->(i:Institution {name: 'University of Cambridge'}) RETURN s.knownName",
        },
    ]

    # Initialize components
    exemplar_selector = ExemplarSelector(exemplars=exemplars)
    post_processor = CypherPostProcessor()
    lru_cache_manager = LRUDataManager(cache_size=128)
    
    # The QueryGenerator requires a predictor. We still define the signature and create a basic predictor for it to use.
    text2cypher_predictor = dspy.ChainOfThought(Text2Cypher)
    query_generator = QueryGenerator(conn=conn, text2cypher_predictor=text2cypher_predictor)


    return (
        exemplar_selector,
        exemplars,
        lru_cache_manager,
        post_processor,
        query_generator,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""We still need the schema definition and pruning logic from the original notebook.""")
    return


@app.cell
def _(kuzu):
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
    return (get_schema_dict,)


@app.cell
def _(BaseModel, Field):
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
    return GraphSchema, Query


@app.cell
def _(GraphSchema, dspy):
    class PruneSchema(dspy.Signature):
        """
        Understand the given labelled property graph schema and the given user question. Your task
        is to return ONLY the subset of the schema (node labels, edge labels and properties) that is
        relevant to the question.
        """
        question: str = dspy.InputField()
        input_schema: str = dspy.InputField()
        pruned_schema: GraphSchema = dspy.OutputField()
    return (PruneSchema,)


@app.cell
def _(Query, dspy):
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
    return (Text2Cypher,)


@app.cell
def _(mo):
    sample_question_ui = mo.ui.text(
        value="Which scholars won prizes in Physics and were affiliated with University of Cambridge?",
        label="## Enter Your Question",
        full_width=True,
    )
    return sample_question_ui





@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Full Pipeline Execution
    The cell below runs the entire advanced pipeline:
    1. Prunes the schema.
    2. Checks for a cached query.
    3. If cache misses, it selects exemplars, generates/refines the query, and post-processes it.
    4. Stores the new query in the cache.
    5. Displays the final query and metadata.
    """)
    return


@app.cell
def _(
    PruneSchema,
    conn,
    dspy,
    exemplar_selector,
    get_schema_dict,
    json,
    lru_cache_manager,
    mo,
    post_processor,
    query_generator,
    sample_question_ui,
):
    
    import json
    sample_question = sample_question_ui.value
    # Prune Schema
    input_schema = get_schema_dict(conn)
    prune = dspy.ChainOfThought(PruneSchema)
    pruned_schema_result = prune(question=sample_question, input_schema=json.dumps(input_schema, indent=2))
    pruned_schema = pruned_schema_result.pruned_schema.model_dump()

    # --- Start of Integrated Pipeline ---

    # 1. Check cache
    schema_str = json.dumps(pruned_schema, sort_keys=True)
    cache_key = f"{sample_question}|{schema_str}"
    cached_query = lru_cache_manager.get_data(lru_cache_manager._hash(cache_key))

    query_history = []
    applied_rules = []

    if cached_query:
        final_query = cached_query
        cache_status = "HIT"
    else:
        cache_status = "MISS"
        # 2. Get dynamic exemplars
        top_k_exemplars = exemplar_selector.select_top_k(sample_question, k=2)

        # 3. Generate query with refinement
        generated_query, query_history = query_generator.generate_with_refinement(
            question=sample_question, schema=json.dumps(pruned_schema, indent=2), examples=str(top_k_exemplars)
        )

        # 4. Post-process the query
        final_query = post_processor.process(generated_query)
        applied_rules = post_processor.get_applied_rules()

        # 5. Set cache
        lru_cache_manager.set_data(lru_cache_manager._hash(cache_key), final_query)

    # --- End of Integrated Pipeline ---

    # Display pipeline outputs
    mo.vstack([
        mo.md(f"**Cache Status:** {cache_status}"),
        mo.md(f"### Final Cypher Query:"),
        mo.md(f"""```cypher
        {final_query}
        ```"""),
        mo.md(f"**Post-processing Rules Applied:** `{applied_rules}`") if applied_rules else None,
        mo.md(f"**Query Generation History:**") if query_history else None,
        *[mo.md(f"  - Attempt {i+1}: `{q}`") for i, q in enumerate(query_history) if query_history],
        lru_cache_manager.display_cache_info(),
    ])

    return final_query, sample_question


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Query Execution and Final Answer
    Finally, we execute the query and use the results as context to generate a natural language answer.
    """)
    return


@app.cell
def _(dspy):
    class AnswerQuestion(dspy.Signature):
        """
        - Use the provided question, the generated Cypher query and the context to answer the question.
        - If the context is empty, state that you don't have enough information to answer the question.
        """
        question: str = dspy.InputField()
        cypher_query: str = dspy.InputField()
        context: str = dspy.InputField()
        response: str = dspy.OutputField()
    return (AnswerQuestion,)


@app.cell
def _(AnswerQuestion, conn, dspy, final_query, mo, sample_question):
    outputs = []
    # Execute the final query
    try:
        result = conn.execute(final_query)
        context = [item for row in result.get_as_df().values for item in row]
        outputs.append(mo.md("**Query Result:**"))
        outputs.append(mo.md(f"`{context}`").callout())
    except RuntimeError as e:
        context = None
        outputs.append(mo.md(f"**Error running query:** {e}"))

    # Generate the final answer
    if context is None:
        outputs.append(mo.md("Could not generate an answer due to a query error."))
    else:
        answer_generator = dspy.ChainOfThought(AnswerQuestion)
        answer = answer_generator(
            question=sample_question, cypher_query=final_query, context=str(context)
        )
        outputs.append(mo.md("**Final Answer:**"))
        outputs.append(mo.md(f"> {answer.response}"))
    
    mo.vstack(outputs)


@app.cell
def _():
    import os
    import marimo as mo
    import kuzu
    import dspy
    from typing import Any
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
    from dspy.adapters.baml_adapter import BAMLAdapter
    from text_2_cypher import (
        ExemplarSelector,
        QueryGenerator,
        CypherPostProcessor,
    )
    from cache_method import LRUDataManager
    return (
        Any,
        BAMLAdapter,
        BaseModel,
        CypherPostProcessor,
        ExemplarSelector,
        Field,
        LRUDataManager,
        QueryGenerator,
        dspy,
        kuzu,
        load_dotenv,
        mo,
        os,
    )


if __name__ == "__main__":
    app.run()

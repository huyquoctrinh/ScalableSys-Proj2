import marimo
import time

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        rf"""
    # Graph RAG using Text2Cypher

    This is a demo app in marimo that allows you to query the Nobel laureate graph (that's managed in Kuzu) using natural language. A language model takes in the question you enter, translates it to Cypher via a custom Text2Cypher pipeline in Kuzu that's powered by DSPy. The response retrieved from the graph database is then used as context to formulate the answer to the question.

    > \- Powered by Kuzu, DSPy and marimo \-
    """
    )
    return


@app.cell
def _(mo):
    text_ui = mo.ui.text(value="Which scholars won prizes in Physics and were affiliated with University of Cambridge?", full_width=True)
    return (text_ui,)


@app.cell
def _(text_ui):
    text_ui
    return


@app.cell
def _(KuzuDatabaseManager, LRUDataManager, mo, run_graph_rag, text_ui):
    db_name = "nobel.kuzu"
    db_manager = KuzuDatabaseManager(db_name)
    cache_manager = LRUDataManager(cache_size=256)

    question = text_ui.value

    with mo.status.spinner(title="Generating answer...") as _spinner:
        result = run_graph_rag([question], db_manager, cache_manager)[0]

    query = result['query']
    answer = result['answer'].response
    return answer, query


@app.cell
def _(answer, mo, query):
    mo.hstack([mo.md(f"""### Query\n```{query}```"""), mo.md(f"""### Answer\n{answer}""")])
    return


@app.cell
def _(GraphSchema, Query, dspy):
    class PruneSchema(dspy.Signature):
        """
        Understand the given labelled property graph schema and the given user question. Your task
        is to return ONLY the subset of the schema (node labels, edge labels and properties) that is
        relevant to the question.
            - The schema is a list of nodes and edges in a property graph.
            - The nodes are the entities in the graph.
            - The edges are the relationships between the nodes.
            - Properties of nodes and edges are their attributes, which helps answer the question.
        """

        question: str = dspy.InputField()
        input_schema: str = dspy.InputField()
        pruned_schema: GraphSchema = dspy.OutputField()


    class Text2Cypher(dspy.Signature):
        """
        Translate the question into a valid Cypher query that respects the graph schema.
        Use the provided examples as reference for query patterns.

        <EXAMPLES>
        {examples}
        </EXAMPLES>

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
        examples: str = dspy.InputField()
        query: Query = dspy.OutputField()


    class AnswerQuestion(dspy.Signature):
        """
        - Use the provided question, the generated Cypher query and the context to answer the question.
        - If the context is empty, state that you don't have enough information to answer the question.
        - When dealing with dates, mention the month in full.
        """

        question: str = dspy.InputField()
        cypher_query: str = dspy.InputField()
        context: str = dspy.InputField()
        response: str = dspy.OutputField()
    return AnswerQuestion, PruneSchema, Text2Cypher


@app.cell
def _(BAMLAdapter, OPENROUTER_API_KEY, dspy):
    # Using OpenRouter. Switch to another LLM provider as needed
    lm = dspy.LM(
        model="openrouter/google/gemini-2.0-flash-001",
        api_base="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    dspy.configure(lm=lm, adapter=BAMLAdapter())
    return


@app.cell
def _(kuzu):
    class KuzuDatabaseManager:
        """Manages Kuzu database connection and schema retrieval."""

        def __init__(self, db_path: str = "nobel.kuzu"):
            self.db_path = db_path
            self.db = kuzu.Database(db_path, read_only=True)
            self.conn = kuzu.Connection(self.db)

        @property
        def get_schema_dict(self) -> dict[str, list[dict]]:
            response = self.conn.execute("CALL SHOW_TABLES() WHERE type = 'NODE' RETURN *;")
            nodes = [row[1] for row in response]  # type: ignore
            response = self.conn.execute("CALL SHOW_TABLES() WHERE type = 'REL' RETURN *;")
            rel_tables = [row[1] for row in response]  # type: ignore
            relationships = []
            for tbl_name in rel_tables:
                response = self.conn.execute(f"CALL SHOW_CONNECTION('{tbl_name}') RETURN *;")
                for row in response:
                    relationships.append({"name": tbl_name, "from": row[0], "to": row[1]})  # type: ignore
            schema = {"nodes": [], "edges": []}

            for node in nodes:
                node_schema = {"label": node, "properties": []}
                node_properties = self.conn.execute(f"CALL TABLE_INFO('{node}') RETURN *;")
                for row in node_properties:  # type: ignore
                    node_schema["properties"].append({"name": row[1], "type": row[2]})  # type: ignore
                schema["nodes"].append(node_schema)

            for rel in relationships:
                edge = {
                    "label": rel["name"],
                    "from": rel["from"],
                    "to": rel["to"],
                    "properties": [],
                }
                rel_properties = self.conn.execute(f"""CALL TABLE_INFO('{rel["name"]}') RETURN *;""")
                for row in rel_properties:  # type: ignore
                    edge["properties"].append({"name": row[1], "type": row[2]})  # type: ignore
                schema["edges"].append(edge)
            return schema
    return (KuzuDatabaseManager,)


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
        from_: Node = Field(alias="from", description="Source node label")
        to: Node = Field(alias="to", description="Target node label")
        properties: list[Property] | None


    class GraphSchema(BaseModel):
        nodes: list[Node]
        edges: list[Edge]
    return GraphSchema, Query


@app.cell
def _(
    AnswerQuestion,
    Any,
    CypherPostProcessor,
    ExemplarSelector,
    KuzuDatabaseManager,
    LRUDataManager,
    PruneSchema,
    Query,
    QueryGenerator,
    Text2Cypher,
    dspy,
    json,
):
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
    ]

    class EnhancedGraphRAG(dspy.Module):
        """
        DSPy custom module that applies Text2Cypher to generate a query and run it
        on the Kuzu database, to generate a natural language response.
        """

        def __init__(self, db_manager: KuzuDatabaseManager, cache_manager: LRUDataManager):
            self.prune = dspy.Predict(PruneSchema)
            self.text2cypher = dspy.Predict(Text2Cypher)
            self.generate_answer = dspy.ChainOfThought(AnswerQuestion)
            self.exemplar_selector = ExemplarSelector(exemplars)
            self.query_generator = QueryGenerator(db_manager.conn, self.text2cypher)
            self.post_processor = CypherPostProcessor()
            self.cache_manager = cache_manager

        def get_cypher_query(self, question: str, input_schema: str) -> Query:
            prune_result = self.prune(question=question, input_schema=input_schema)
            schema = prune_result.pruned_schema

            selected_examples = self.exemplar_selector.select_top_k(question, k=3)
            examples_text = "\n\n".join([
                f"Question: {ex['question']}\nCypher: {ex['cypher']}"
                for ex in selected_examples
            ])

            query, _ = self.query_generator.generate_with_refinement(
                question=question,
                schema=str(schema),
                examples=examples_text
            )

            final_query = self.post_processor.process(query)
            return final_query

        def run_query(
            self, db_manager: KuzuDatabaseManager, question: str, input_schema: str
        ) -> tuple[str, list[Any] | None]:
            """
            Run a query synchronously on the database with LRU caching.
            Cache key includes both question and schema for accuracy.
            """
            # Create cache key from question and input schema
            import json
            cache_key = f"{question}|{json.dumps(input_schema, sort_keys=True)}"
            
            cached_result = self.cache_manager.get_data(cache_key)
            if cached_result:
                print("✓ Cache hit! Using cached query and results.")
                return cached_result["query"], cached_result["results"]

            print("✗ Cache miss. Generating new query...")
            query = self.get_cypher_query(question=question, input_schema=input_schema)
            try:
                # Run the query on the database
                result = db_manager.conn.execute(query)
                results = [item for row in result for item in row]
                self.cache_manager.set_data(cache_key, {"query": query, "results": results})
                print(f"✓ Query cached. Cache size: {len(self.cache_manager.cache)}/{self.cache_manager.cache.maxsize}")
            except RuntimeError as e:
                print(f"✗ Error running query: {e}")
                results = None
            return query, results

        def forward(self, db_manager: KuzuDatabaseManager, question: str, input_schema: str):
            final_query, final_context = self.run_query(db_manager, question, input_schema)
            if final_context is None:
                print("Empty results obtained from the graph database. Please retry with a different question.")
                return {}
            else:
                answer = self.generate_answer(
                    question=question, cypher_query=final_query, context=str(final_context)
                )
                response = {
                    "question": question,
                    "query": final_query,
                    "answer": answer,
                }
                return response

        async def aforward(self, db_manager: KuzuDatabaseManager, question: str, input_schema: str):
            final_query, final_context = self.run_query(db_manager, question, input_schema)
            if final_context is None:
                print("Empty results obtained from the graph database. Please retry with a different question.")
                return {}
            else:
                answer = self.generate_answer(
                    question=question, cypher_query=final_query, context=str(final_context)
                )
                response = {
                    "question": question,
                    "query": final_query,
                    "answer": answer,
                }
                return response
        def measure_pipeline(self, db_manager, question: str, input_schema: str, token_counter=None) -> dict:
            # token counter
            if token_counter is None:
                token_counter = getattr(self, "_default_token_counter", None)
                if token_counter is None:
                    def _fallback_tok(s: str) -> int:
                        try:
                            import tiktoken
                            enc = tiktoken.get_encoding("cl100k_base")
                            return len(enc.encode(s))
                        except Exception:
                            return max(1, len(s) // 4)
                    token_counter = _fallback_tok

            # 1) prune
            t0 = time.perf_counter()
            pr = self.prune(question=question, input_schema=input_schema)
            t_prune = time.perf_counter() - t0
            pruned = pr.pruned_schema.model_dump_json()

            # 2) text2cypher
            t1 = time.perf_counter()
            t2c = self.text2cypher(question=question, input_schema=pruned)
            t_t2c = time.perf_counter() - t1

            try:
                query_str = t2c.query.query
            except AttributeError:
                query_str = getattr(t2c, "query", None) or str(t2c)

            t2c_out_tok = token_counter(query_str)
            t2c_tps = t2c_out_tok / t_t2c if t_t2c > 0 else float("inf")

            # 3) DB execute (+ fetch)
            t2 = time.perf_counter()
            try:
                res = db_manager.conn.execute(query_str)
                rows = [item for row in res for item in row]
            except RuntimeError:
                rows = None
            t_db = time.perf_counter() - t2

            # 4) answer
            t3 = time.perf_counter()
            ans = self.generate_answer(question=question, cypher_query=query_str, context=str(rows))
            t_ans = time.perf_counter() - t3
            try:
                ans_text = ans.response
            except AttributeError:
                ans_text = str(ans)
            ans_tok = token_counter(ans_text)
            ans_tps = ans_tok / t_ans if t_ans > 0 else float("inf")

            total = t_prune + t_t2c + t_db + t_ans

            return {
                "question": question,
                "query": query_str,
                "prune_s": t_prune,
                "t2c_s": t_t2c,
                "db_s": t_db,
                "answer_s": t_ans,
                "total_s": total,
                "t2c_output_tokens": t2c_out_tok,
                "t2c_tokens_per_s": t2c_tps,
                "answer_output_tokens": ans_tok,
                "answer_tokens_per_s": ans_tps,
                "result_items": 0 if rows is None else len(rows),
            }

    def run_graph_rag(questions: list[str], db_manager: KuzuDatabaseManager, cache_manager: LRUDataManager) -> list[Any]:
        schema = str(db_manager.get_schema_dict)
        rag = EnhancedGraphRAG(db_manager, cache_manager)
        # Run pipeline
        results = []
        for question in questions:
            response = rag(db_manager=db_manager, question=question, input_schema=schema)
            results.append(response)
        return results

    return (run_graph_rag,)

@app.cell
def _(GraphRAG, KuzuDatabaseManager, json):
    def bench_t2c(db_path: str = "nobel.kuzu", question: str = None):
        """
        Headless-style timing for Text2Cypher only.
        Prints one line with latency and throughput. Returns the metrics dict.
        """
        if question is None:
            question = "Which scholars won prizes in Physics and were affiliated with University of Cambridge?"

        dbm = KuzuDatabaseManager(db_path)
        schema = json.dumps(dbm.get_schema_dict)
        rag = GraphRAG()

        m = rag.measure_text2cypher(question=question, input_schema=schema)
        print(f"[T2C] {m['t2c_time_s']:.3f}s | {m['t2c_output_tokens']} tok | {m['t2c_tokens_per_s']:.2f} tok/s")
        return m
    return (bench_t2c,)

@app.cell
def _(bench_t2c, stats):

    def bench_t2c_stats(db_path: str = "nobel.kuzu",
                        question: str | None = None,
                        runs: int = 3):
        times, tokens, tps = [], [], []
        for i in range(runs):
            m = bench_t2c(db_path=db_path, question=question)  # prints per-run line
            times.append(m["t2c_time_s"])
            tokens.append(m["t2c_output_tokens"])
            tps.append(m["t2c_tokens_per_s"])

        def mean_sd(xs):
            mean = stats.mean(xs)
            sd = stats.stdev(xs) if len(xs) > 1 else 0.0
            return mean, sd

        mt, sdt = mean_sd(times)
        mk, sdk = mean_sd(tokens)
        mr, sdr = mean_sd(tps)

        print(f"[T2C][summary over {runs} runs] "
              f"time: {mt:.4f}s ± {sdt:.4f}s | "
              f"tokens: {mk:.2f} ± {sdk:.2f} | "
              f"tokens/s: {mr:.2f} ± {sdr:.2f}")

        return {
            "runs": runs,
            "per_run": {"time_s": times, "tokens": tokens, "tokens_per_s": tps},
            "mean": {"time_s": mt, "tokens": mk, "tokens_per_s": mr},
            "stdev": {"time_s": sdt, "tokens": sdk, "tokens_per_s": sdr},
        }

    return (bench_t2c_stats,)

@app.cell
def _():
    return


@app.cell
def _():
    import marimo as mo
    import os
    from textwrap import dedent
    from typing import Any

    import dspy
    import kuzu
    from dotenv import load_dotenv
    from dspy.adapters.baml_adapter import BAMLAdapter
    from pydantic import BaseModel, Field
    from cache_method import LRUDataManager
    from text_2_cypher import ExemplarSelector, QueryGenerator, CypherPostProcessor


    load_dotenv()

    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    return (
        Any,
        BAMLAdapter,
        BaseModel,
        CypherPostProcessor,
        ExemplarSelector,
        Field,
        KuzuDatabaseManager,
        LRUDataManager,
        OPENROUTER_API_KEY,
        QueryGenerator,
        dspy,
        kuzu,
        mo,
        json,
    )

@app.cell
def _(GraphRAG, KuzuDatabaseManager, json, stats):
    import csv, datetime, pathlib
    def bench_pipeline_csv(path="tests/questions.csv",
                           db_path="nobel.kuzu",
                           runs=3,
                           save_csv=True,
                           save_png=True):
        dbm = KuzuDatabaseManager(db_path)
        schema = json.dumps(dbm.get_schema_dict)
        rag = GraphRAG()

        # load CSV
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if r.get("question")]

        # validate header
        if not rows or "question" not in rows[0]:
            raise ValueError("CSV must have at least a 'question' column.")

        results = []
        for r in rows:
            q = r["question"].strip()
            per = []
            for _ in range(runs):
                m = rag.measure_pipeline(db_manager=dbm, question=q, input_schema=schema)
                per.append(m)
                print(
                    f"[PIPE] {q[:60]}... | prune {m['prune_s']:.3f}s | t2c {m['t2c_s']:.3f}s | "
                    f"db {m['db_s']:.3f}s | ans {m['answer_s']:.3f}s | total {m['total_s']:.3f}s | "
                    f"t2c {m['t2c_tokens_per_s']:.2f} tok/s | ans {m['answer_tokens_per_s']:.2f} tok/s"
                )

            def mean_sd(xs):
                mu = stats.mean(xs)
                sd = stats.stdev(xs) if len(xs) > 1 else 0.0
                return mu, sd

            mt_pr, sd_pr   = mean_sd([x["prune_s"] for x in per])
            mt_t2c, sd_t2c = mean_sd([x["t2c_s"] for x in per])
            mt_db, sd_db   = mean_sd([x["db_s"] for x in per])
            mt_ans, sd_ans = mean_sd([x["answer_s"] for x in per])
            mt_tot, sd_tot = mean_sd([x["total_s"] for x in per])
            mt_tps, sd_tps = mean_sd([x["t2c_tokens_per_s"] for x in per])

            results.append({
                "question": q,
                "tag": r.get("tag", ""),
                "prune_s_mean": mt_pr, "prune_s_sd": sd_pr,
                "t2c_s_mean": mt_t2c, "t2c_s_sd": sd_t2c,
                "db_s_mean": mt_db, "db_s_sd": sd_db,
                "answer_s_mean": mt_ans, "answer_s_sd": sd_ans,
                "total_s_mean": mt_tot, "total_s_sd": sd_tot,
                "t2c_tokps_mean": mt_tps, "t2c_tokps_sd": sd_tps,
            })

            # optional quick bar chart
            if save_png:
                try:
                    import matplotlib.pyplot as plt
                    stages = ["prune", "t2c", "db", "answer"]
                    means  = [mt_pr, mt_t2c, mt_db, mt_ans]
                    fig, ax = plt.subplots(figsize=(6, 3))
                    ax.bar(stages, means)
                    ax.set_ylabel("seconds")
                    ax.set_title(q[:50] + "...")
                    pathlib.Path("bench").mkdir(exist_ok=True)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_png = f"bench/pipeline_{ts}.png"
                    plt.tight_layout()
                    plt.savefig(out_png)
                    plt.close(fig)
                    print(f"saved chart: {out_png}")
                except Exception as e:
                    print(f"chart skipped: {e}")

        # dataset means
        if results:
            mt = stats.mean([r["total_s_mean"] for r in results])
            mk = stats.mean([r["t2c_s_mean"] for r in results])
            print(f"[DATASET MEAN] total: {mt:.4f}s | t2c: {mk:.4f}s")

        # save CSV
        if results and save_csv:
            pathlib.Path("bench").mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = f"bench/pipeline_{ts}.csv"
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                w.writeheader()
                w.writerows(results)
            print(f"saved: {out_path}")

        return results
    return (bench_pipeline_csv,)

@app.cell
def _(bench_pipeline_csv):
    bench_pipeline_csv(
        path="tests/questions.csv",
        db_path="nobel.kuzu",
        runs=3
    )
    return ()

if __name__ == "__main__":
    app.run()

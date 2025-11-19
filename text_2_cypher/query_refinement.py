import dspy
import kuzu
from pydantic import BaseModel, Field

class Query(BaseModel):
    query: str = Field(description="Valid Cypher query with no newlines")

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

class QueryGenerator:
    def __init__(self, conn, text2cypher_predictor, max_iterations=3):
        self.conn = conn
        self.max_iterations = max_iterations
        self.text2cypher = text2cypher_predictor
        self.repair = dspy.ChainOfThought(RepairCypher)
    
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
        error_msg = None
        
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

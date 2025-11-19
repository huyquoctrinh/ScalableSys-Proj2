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
        pattern = r"WHERE\s+(\w+)\.(\w+)\s*=\s*['"]([^'"]+)['"]"
        
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

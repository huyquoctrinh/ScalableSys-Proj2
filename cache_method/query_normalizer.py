"""
Query Normalizer for improved cache hit rates.
Normalizes questions to catch trivial variations.
"""

import re
from typing import Dict


class QueryNormalizer:
    """Normalize queries for consistent caching."""
    
    # Common contractions to expand
    CONTRACTIONS: Dict[str, str] = {
        "who's": "who is",
        "what's": "what is",
        "where's": "where is",
        "when's": "when is",
        "why's": "why is",
        "how's": "how is",
        "won't": "will not",
        "can't": "cannot",
        "couldn't": "could not",
        "shouldn't": "should not",
        "wouldn't": "would not",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "haven't": "have not",
        "hasn't": "has not",
        "hadn't": "had not",
    }
    
    @classmethod
    def normalize(cls, question: str) -> str:
        """
        Normalize question for consistent caching.
        
        Args:
            question: Raw user question
            
        Returns:
            Normalized question string
            
        Examples:
            >>> QueryNormalizer.normalize("Who won Physics?")
            'who won physics'
            
            >>> QueryNormalizer.normalize("Who  won   physics  ?")
            'who won physics'
            
            >>> QueryNormalizer.normalize("Who's won Physics?")
            'who is won physics'
        """
        if not question or not question.strip():
            return ""
        
        # Step 1: Lowercase
        question = question.lower().strip()
        
        # Step 2: Expand contractions
        for contraction, expansion in cls.CONTRACTIONS.items():
            question = question.replace(contraction, expansion)
        
        # Step 3: Remove extra whitespace
        question = re.sub(r'\s+', ' ', question)
        
        # Step 4: Remove punctuation at end
        question = question.rstrip('?.!,;:')
        
        # Step 5: Normalize common patterns
        # "the" at beginning (optional)
        question = re.sub(r'^the\s+', '', question)
        
        # Multiple question marks
        question = re.sub(r'\?+', '?', question)
        
        return question.strip()
    
    @classmethod
    def normalize_verbose(cls, question: str) -> Dict[str, str]:
        """
        Normalize with step-by-step info for debugging.
        
        Returns:
            Dict with original, normalized, and steps applied
        """
        original = question
        steps = []
        
        # Track each step
        if not question or not question.strip():
            return {
                "original": original,
                "normalized": "",
                "steps": ["empty_input"]
            }
        
        # Lowercase
        question = question.lower().strip()
        if question != original:
            steps.append("lowercase")
        
        # Contractions
        for contraction in cls.CONTRACTIONS:
            if contraction in question:
                question = question.replace(contraction, cls.CONTRACTIONS[contraction])
                steps.append(f"expanded_{contraction}")
        
        # Whitespace
        old_q = question
        question = re.sub(r'\s+', ' ', question)
        if question != old_q:
            steps.append("normalized_whitespace")
        
        # Punctuation
        old_q = question
        question = question.rstrip('?.!,;:')
        if question != old_q:
            steps.append("removed_trailing_punctuation")
        
        # The
        if question.startswith('the '):
            question = question[4:]
            steps.append("removed_leading_the")
        
        return {
            "original": original,
            "normalized": question.strip(),
            "steps": steps
        }


def test_normalizer():
    """Test the query normalizer."""
    test_cases = [
        ("Who won Physics?", "who won physics"),
        ("Who  won   physics  ?", "who won physics"),
        ("Who's won Physics?", "who is won physics"),
        ("The scholars who won prizes", "scholars who won prizes"),
        ("WHAT'S THE ANSWER???", "what is the answer"),
        ("Can't   find   it!!", "cannot find it"),
        ("  Trailing spaces  ", "trailing spaces"),
    ]
    
    print("Testing QueryNormalizer:")
    print("="*70)
    
    passed = 0
    for input_q, expected in test_cases:
        result = QueryNormalizer.normalize(input_q)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        
        print(f"[{status}] Input:    '{input_q}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print()
    
    print("="*70)
    print(f"Passed: {passed}/{len(test_cases)}")
    
    # Show verbose example
    print("\nVerbose normalization example:")
    verbose = QueryNormalizer.normalize_verbose("Who's  won the Physics prize???")
    print(f"Original:   {verbose['original']}")
    print(f"Normalized: {verbose['normalized']}")
    print(f"Steps:      {', '.join(verbose['steps'])}")


if __name__ == "__main__":
    test_normalizer()


"""
Alternative ExemplarSelector using neural embeddings (Sentence Transformers)
for better semantic similarity matching.

Usage:
    Replace the import in your code:
    from text_2_cypher.exemplar_selector_neural import ExemplarSelector
"""

from sentence_transformers import SentenceTransformer
import numpy as np

class ExemplarSelector:
    """
    Selects relevant exemplars using dense neural embeddings.
    Better semantic understanding than TF-IDF, but slower.
    """
    def __init__(self, exemplars, model_name='all-MiniLM-L6-v2'):
        """
        Args:
            exemplars: List of example question-cypher pairs
            model_name: Sentence transformer model to use
                - 'all-MiniLM-L6-v2': Fast, 384 dims (recommended)
                - 'all-mpnet-base-v2': More accurate, 768 dims (slower)
        """
        self.exemplars = exemplars
        self.model = SentenceTransformer(model_name)
        
        # Pre-compute embeddings for all exemplar questions
        self.exemplar_questions = [ex['question'] for ex in exemplars]
        print(f"Computing neural embeddings for {len(self.exemplar_questions)} exemplars...")
        self.exemplar_embeddings = self.model.encode(
            self.exemplar_questions,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        print(f"✓ Embeddings computed: {self.exemplar_embeddings.shape}")
    
    def select_top_k(self, question: str, k: int = 3) -> list[dict]:
        """
        Select top-k most similar exemplars using cosine similarity.
        
        Args:
            question: User's question
            k: Number of exemplars to return
            
        Returns:
            List of top-k most similar exemplar dictionaries
        """
        # Encode the input question
        question_embedding = self.model.encode(
            [question],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        # Compute cosine similarity
        similarities = np.dot(self.exemplar_embeddings, question_embedding) / (
            np.linalg.norm(self.exemplar_embeddings, axis=1) * 
            np.linalg.norm(question_embedding)
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return selected exemplars with similarity scores
        selected = []
        for idx in top_k_indices:
            exemplar = self.exemplars[idx].copy()
            exemplar['similarity_score'] = float(similarities[idx])
            selected.append(exemplar)
        
        return selected


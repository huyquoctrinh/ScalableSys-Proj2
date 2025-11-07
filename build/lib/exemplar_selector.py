from sentence_transformers import SentenceTransformer
import numpy as np

class ExemplarSelector:
    def __init__(self, exemplars, model_name='all-MiniLM-L6-v2'):
        self.exemplars = exemplars
        self.model = SentenceTransformer(model_name)
        
        # Pre-compute embeddings for all exemplar questions
        self.exemplar_questions = [ex['question'] for ex in exemplars]
        self.exemplar_embeddings = self.model.encode(self.exemplar_questions)
    
    def select_top_k(self, question: str, k: int = 3) -> list[dict]:
        """Select top-k most similar exemplars"""
        # Encode the input question
        question_embedding = self.model.encode([question])[0]
        
        # Compute cosine similarity
        similarities = np.dot(self.exemplar_embeddings, question_embedding) / (
            np.linalg.norm(self.exemplar_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return selected exemplars
        return [self.exemplars[i] for i in top_k_indices]

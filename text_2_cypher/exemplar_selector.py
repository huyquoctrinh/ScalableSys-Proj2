from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ExemplarSelector:
    def __init__(self, exemplars):
        self.exemplars = exemplars
        self.vectorizer = TfidfVectorizer()
        
        # Pre-compute embeddings for all exemplar questions
        self.exemplar_questions = [ex['question'] for ex in exemplars]
        self.exemplar_embeddings = self.vectorizer.fit_transform(self.exemplar_questions)
    
    def select_top_k(self, question: str, k: int = 3) -> list[dict]:
        """Select top-k most similar exemplars"""
        # Encode the input question
        question_embedding = self.vectorizer.transform([question])
        
        # Compute cosine similarity
        similarities = cosine_similarity(question_embedding, self.exemplar_embeddings).flatten()
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return selected exemplars
        return [self.exemplars[i] for i in top_k_indices]
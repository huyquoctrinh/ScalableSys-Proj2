from .data_manager import DataManager
from hashlib import sha256

class LRUDataManager(DataManager):
    def __init__(self, cache_size=256):
        super().__init__(cache_size=cache_size)
        # Additional initialization for LRUDataManager can be added here
    def display_cache_info(self):
        print(f"LRU Cache Size: {self.cache.maxsize}, Current Items: {len(self.cache)}")
    
    def _hash(self, data):
        """Generate a SHA-256 hash for the given data."""
        return sha256(repr(data).encode()).hexdigest()
    
    def process_value(self, retrieved_value, answer, embedding):
        return {
            "retrieved_value": retrieved_value,
            "answer": answer,
            "embedding": embedding
        }
    
    def process_record(self, record):
        key = record.get("key")
        value = record.get("value")
        hashed_key = self._hash(key)
        retrieved_value = value["value"]
        answer = value.get("answer")
        embedding = value.get("embedding")
        stored_value = self.process_value(retrieved_value, answer, embedding)
        self.set_data(hashed_key, stored_value)


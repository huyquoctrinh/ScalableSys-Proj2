from cache_method import LRUDataManager
import numpy as np
import pytest

def test_lru_data_manager_initialization():
    lru_manager = LRUDataManager(cache_size=100)
    assert lru_manager.cache.maxsize == 100
    assert len(lru_manager.cache) == 0

def test_lru_data_manager_set_and_get_data():
    lru_manager = LRUDataManager(cache_size=2)
    lru_manager.set_data("key1", "value1")
    lru_manager.set_data("key2", "value2")
    assert lru_manager.get_data("key1") == "value1"

def test_lru_ingest_record():
    lru_manager = LRUDataManager(cache_size=2)
    record = {
        "key": "sample_key",
        "value": {
            "value": "sample_value",
            "answer": "sample_answer",
            "embedding": [0.1, 0.2, 0.3]
        }
    }
    lru_manager.process_record(record)
    hashed_key = lru_manager._hash("sample_key")
    stored_value = lru_manager.get_data(hashed_key)
    assert stored_value["retrieved_value"] == "sample_value"
    assert stored_value["answer"] == "sample_answer"
    assert stored_value["embedding"] == [0.1, 0.2, 0.3]


def test_lru_data_manager():
    lru_manager = LRUDataManager(cache_size=512)
    key = "sample_key_2"
    retrieved_value = "sample_retrieved_value"
    answer = "sample_answer_2"
    embedding = np.random.rand(128).tolist()
    processed_value = lru_manager.process_value(retrieved_value, answer, embedding)
    hashed_key = lru_manager._hash(key)
    lru_manager.set_data(hashed_key, processed_value)
    stored_value = lru_manager.get_data(hashed_key)

    assert stored_value["retrieved_value"] == retrieved_value
    assert stored_value["answer"] == answer
    assert stored_value["embedding"] == embedding

def main():
    test_lru_data_manager_initialization()
    test_lru_data_manager_set_and_get_data()
    test_lru_ingest_record()
    test_lru_data_manager()
    print("All tests passed.")  

if __name__ == "__main__":
    main()
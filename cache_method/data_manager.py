from cachetools import LRUCache

def create_data_manager_cache(max_size=128):
    """
    Create and return an LRU cache for data manager.

    Args:
        max_size (int): Maximum size of the cache.
    Returns:
        LRUCache: An instance of LRUCache with the specified maximum size.
    """  
    return LRUCache(maxsize=max_size)       

class DataManager:
    def __init__(self, cache_size=128):
        self.cache = create_data_manager_cache(max_size=cache_size)

    def get_data(self, key):
        return self.cache.get(key)

    def set_data(self, key, value):
        self.cache[key] = value
import logging
logger = logging.getLogger(__name__)

class Cache:
    def __init__(self) -> None:
        self._data = {}
        logger.info("Cache inicializado.")

    def get(self, key, default=None):
        return self._data.get(
            key,
            default
        )
    
    def set(self,key,value):
        self._data[key] = value
    
    def delete(self,key):
        self._data.pop(
            key,
            None
        )
    
    def clear(self):
        self._data.clear()
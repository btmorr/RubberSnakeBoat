from typing import Union


class Store:
    """
    A k-v datastore with basic crud operations

    Currently only supports in-memory storage
    """
    internal: dict = dict()

    def upsert(self, key: str, value: str):
        """Writes a value to the store, without checking for previously
        existing values."""
        self.internal[key] = value

    def read(self, key: str) -> Union[str, None]:
        """Reads the value stored at the specified key. Returns `None` if there
        is no value for the key."""
        return self.internal.get(key)

    def delete(self, key: str):
        """Deletes the entry at the specified key, without checking whether
        it exists."""
        self.internal.pop(key, None)

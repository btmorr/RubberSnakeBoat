class Store:
    """
    A k-v datastore with basic crud operations

    Currently only supports in-memory storage
    """
    internal: dict = dict()

    def upsert(self, key: str, value: str):
        self.internal[key] = value

    def read(self, key: str) -> str | None:
        return self.internal.get(key)

    def delete(self, key: str):
        self.internal.pop(key, None)

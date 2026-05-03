"""
Document storage backed by MongoDB.

Why MongoDB:
    A real production-style document database. Stores JSON-shaped records,
    supports field-level queries, persists data across service restarts,
    and can be accessed by multiple processes simultaneously.

Idempotency: insert() checks if a document with the same image_id already
exists. If yes, the second insert is silently ignored — slide 10's
"duplicate events do not create duplicate state" guarantee.
"""

from pymongo import MongoClient

from app.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION


class DocumentRepository:
    def __init__(self, uri=None, db_name=None, collection_name=None):
        # Allow overrides for tests; default to .env values otherwise.
        self._client = MongoClient(uri or MONGO_URI)
        self._db = self._client[db_name or MONGO_DB_NAME]
        self._collection = self._db[collection_name or MONGO_COLLECTION]

    def insert(self, image_id: str, document: dict) -> bool:
        """
        Save a document. Returns True if saved, False if duplicate.
        Slide 10 idempotency guarantee.
        """
        # check if a document with this image_id already exists

        if self._collection.count_documents({"image_id": image_id}) > 0:
            print(f"[Repository] Skipping duplicate — '{image_id}' already stored.")
            return False

        self._collection.insert_one(document)
        print(f"[Repository] Stored document for '{image_id}'.")
        return True

      


    def get(self, image_id: str) -> dict | None:
        """Fetch a document by image_id. Returns None if not found."""
        # use self._collection.find_one({"image_id": image_id})
        #       It returns the doc dict or None — exactly what we want
        return self._collection.find_one({"image_id": image_id})

    def all(self) -> dict:
        """Return all stored documents as {image_id: doc}."""
        # iterate self._collection.find() and build the dict
        #       Hint: {doc["image_id"]: doc for doc in self._collection.find()}
        return {doc["image_id"]: doc for doc in self._collection.find()}

    def clear(self):
        """Wipe all data (used in tests)."""
        # self._collection.delete_many({})
        #       The empty {} matches everything
        self._collection.delete_many({})
        
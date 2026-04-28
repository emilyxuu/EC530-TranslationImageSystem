from pathlib import Path
from tinydb import TinyDB, Query


class DocumentRepository:
    def __init__(self, db_path="data/documents.json"):
        # Make sure the parent folder exists before TinyDB tries to
        # create the file. mkdir(exist_ok=True) won't error if it's there.
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Open (or create) the database
        self._db = TinyDB(db_path)
        
        # The Query() object is reusable — keep one around
        self._Img = Query()

    def insert(self, image_id: str, document: dict) -> bool:
        """
        Save a document. Returns True if saved, False if duplicate.
        Slide 10 idempotency guarantee.
        """

        if self._db.search(self._Img.image_id == image_id):
            print(f"[Repository] Skipping duplicate — '{image_id}' already stored.")
            return False
        
        
        #otherwise, insert the document and return True
        self._db.insert(document)
        print(f"[Repository] Stored document for '{image_id}'.")
        return True


    def get(self, image_id: str) -> dict | None:
        """Fetch a document by image_id. Returns None if not found."""
        #search for the matching document
        
        results = self._db.search(self._Img.image_id == image_id)
        return results[0] if results else None

    def all(self) -> dict:
        """Return all stored documents as {image_id: doc}."""

        return {doc["image_id"]: doc for doc in self._db.all()}
       


    def clear(self):
        """Wipe all data (used in tests)."""
        
        self._db.truncate()
# Placeholder for MongoDB (Week 2).
#
# Each image gets one document stored under its image_id.
# Built-in idempotency: if the same image_id arrives twice,
# the second insert is silently ignored so we never store duplicates.
#
# The document format matches what DocumentDBService saves:
# {
#   "image_id": "sign_001",
#   "detected_text": "Arrêt",
#   "source_language": "fr",
#   "translation_english": "Stop",
#   "confidence_score": 0.98,
#   "status": "stored",
#   "stored_at": "2026-..."
# }

class InMemoryRepository:

    def __init__(self):
        # Simple dictionary: { image_id (str) -> document (dict) }
        self._store = {}

    def insert(self, image_id: str, document: dict) -> bool:
        """
        Save a document.
        Returns True if it was saved, False if image_id already existed (duplicate).
        """
        if image_id in self._store:
            print(f"[Repository] Skipping duplicate — '{image_id}' already stored.")
            return False

        self._store[image_id] = document
        print(f"[Repository] Stored document for '{image_id}'.")
        return True

    def get(self, image_id: str) -> dict | None:
        """Fetch a document by image_id. Returns None if not found."""
        return self._store.get(image_id)

    def all(self) -> dict:
        """Return all stored documents."""
        return dict(self._store)

    def clear(self):
        """Clears the store in tests between runs."""
        self._store.clear()
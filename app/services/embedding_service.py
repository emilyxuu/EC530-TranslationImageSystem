import json
import random
from pathlib import Path

from app.broker import subscribe_to, publish_message
from app.schemas import create_base_event, is_valid_event
from app.topics import ANNOTATION_STORED, EMBEDDING_CREATED

SERVICE_NAME = "Embedding Service"

# Where the pre-computed embeddings live
DATASET_PATH = Path("app/sample_data/embeddings.json")

# Vector dimensionality — matches what's in embeddings.json
EMBEDDING_DIM = 8


# ---------------------------------------------------------------------------
# Load dataset at startup
# ---------------------------------------------------------------------------

def _load_dataset():
    """Load the pre-computed embeddings from disk. Called once at startup."""
    with open(DATASET_PATH) as f:
        data = json.load(f)
    
    # Build a lookup: image_id -> embedding vector
    image_embeddings = {
        img["image_id"]: img["embedding"]
        for img in data["images"]
    }
    
    print(f"[{SERVICE_NAME}] Loaded {len(image_embeddings)} embeddings from {DATASET_PATH}")
    return image_embeddings


# Load once. This runs when the module is imported, so the dict is ready
# before any event arrives.
_image_embeddings = _load_dataset()


def _find_matching_label_embedding(detected_text, translation_english):
    """
    Try to find a label whose embedding we should use for this image.
    
    Looks in the label_embeddings dictionary for any label that appears in
    either detected_text or translation_english. Returns the embedding if
    found, otherwise None.
    """
    # Reload the label_embeddings from disk (small, fine to re-read once)
    with open(DATASET_PATH) as f:
        data = json.load(f)
    label_embeddings = data["label_embeddings"]
    
    detected_lower = detected_text.lower()
    translated_lower = translation_english.lower()
    
    # Check each label — does it appear in the detected text or translation?
    for label, vector in label_embeddings.items():
        if label in detected_lower or label in translated_lower:
            return vector
    
    return None


def process_event(event_data):
    """Handle an annotation.stored event and publish embedding.created."""
    
    # reject malformed events with is_valid_event
    if not is_valid_event(event_data):
        return
    
    payload = event_data["payload"]
    image_id = payload.get("image_id", "unknown")
    detected_text = payload.get("detected_text", "")
    translation_english = payload.get("translation_english", "")
    
    print(f"[{SERVICE_NAME}] Generating embedding for {image_id}")
    
    # Try the dataset first (curated images like sign_001)
    embedding = _image_embeddings.get(image_id)
    
    # If not in the dataset, try matching by detected text / translation
    if embedding is None:
        embedding = _find_matching_label_embedding(detected_text, translation_english)
    
    # Last resort: random fallback so the pipeline doesn't hard-fail
    if embedding is None:
        embedding = [random.random() for _ in range(EMBEDDING_DIM)]
        print(f"[{SERVICE_NAME}] No match for {image_id}, using random fallback")
    
    # TODO: build the embedding.created event with create_base_event
    #       topic = EMBEDDING_CREATED
    #       payload should contain: image_id, embedding, dim (the vector length)
    new_event =  create_base_event(
            topic = EMBEDDING_CREATED,
            payload = {
                "image_id" : image_id,
                "embedding" : embedding,
                "dim": len(embedding),
            },
        )
    
    
    
    # TODO: publish the event with publish_message
    publish_message(EMBEDDING_CREATED, new_event)
    
    print(f"[{SERVICE_NAME}] Published embedding.created for {image_id}")


if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    subscribe_to(ANNOTATION_STORED, process_event)
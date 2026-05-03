"""
Embedding Service.

Listens for annotation.stored events, encodes the corresponding image
using CLIP, and publishes embedding.created with the 512-dim vector.

CLIP (clip-ViT-B-32) is loaded once at module startup. This takes ~10
seconds the first time but is then cached in memory.

If the image file at payload["path"] doesn't exist or fails to load,
falls back to encoding the OCR-detected text. This keeps the pipeline
working even when the image is missing.
"""

from pathlib import Path

from PIL import Image
from sentence_transformers import SentenceTransformer

from app.broker import subscribe_to, publish_message
from app.schemas import create_base_event, is_valid_event
from app.topics import ANNOTATION_STORED, EMBEDDING_CREATED

SERVICE_NAME = "Embedding Service"

# Load CLIP once at startup. ~10s first time; cached after.
print(f"[{SERVICE_NAME}] Loading CLIP model...")
_model = SentenceTransformer("clip-ViT-B-32")
print(f"[{SERVICE_NAME}] CLIP loaded ({_model.get_sentence_embedding_dimension()} dim)")


def _encode_image(path: str):
    """Try to encode an image file. Returns the embedding list, or None."""
    try:
        image = Image.open(path).convert("RGB")
        embedding = _model.encode(image).tolist()
        return embedding
    except FileNotFoundError:
        print(f"[{SERVICE_NAME}] Image not found at {path}")
        return None
    except Exception as e:
        print(f"[{SERVICE_NAME}] Failed to encode image at {path}: {e}")
        return None


def _encode_text(text: str):
    """Encode a text string. Used as fallback when image isn't available."""
    return _model.encode(text).tolist()


def process_event(event_data):
    """Handle an annotation.stored event and publish embedding.created."""

    if not is_valid_event(event_data):
        print(f"[{SERVICE_NAME}] ERROR: Malformed event. Dropping.")
        return

    payload = event_data["payload"]
    image_id = payload.get("image_id", "unknown")
    path = payload.get("path", "")
    detected_text = payload.get("detected_text", "")
    translation_english = payload.get("translation_english", "")

    print(f"[{SERVICE_NAME}] Generating embedding for {image_id}")

    # Try real image first
    embedding = _encode_image(path) if path else None

    # Fallback: encode the OCR text (or translation, since they're stubbed
    # to the same value, either works)
    if embedding is None:
        text_to_encode = detected_text or translation_english or "unknown"
        print(f"[{SERVICE_NAME}] Falling back to text encoding: {text_to_encode!r}")
        embedding = _encode_text(text_to_encode)

    new_event = create_base_event(
        topic=EMBEDDING_CREATED,
        payload={
            "image_id": image_id,
            "embedding": embedding,
            "dim": len(embedding),
        },
    )

    publish_message(EMBEDDING_CREATED, new_event)
    print(f"[{SERVICE_NAME}] Published embedding.created for {image_id}")


if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    subscribe_to(ANNOTATION_STORED, process_event)
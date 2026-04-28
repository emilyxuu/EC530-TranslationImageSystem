
from datetime import datetime, timezone


from app.broker import subscribe_to, publish_message
from app.schemas import is_valid_event, create_base_event
from app.repository import InMemoryRepository
from app.topics import INFERENCE_COMPLETED, ANNOTATION_STORED

SERVICE_NAME = "Document DB Service"

# One shared repository instance for this process
# Need to swap this out for a real MongoDB client
repo = InMemoryRepository()

def process_event(event_data: dict):
    """Called every time an inference.completed message arrives."""

    # Drop anything missing a payload
    if not is_valid_event(event_data):
        print(f"[{SERVICE_NAME}] ERROR: Malformed event. Dropping.")
        return

    payload = event_data["payload"] # This is the part of the message that has all the info about the image and annotations
    image_id = payload.get("image_id", "unknown") # Get the image_id or use "unknown" if it's missing. We use image_id as the unique identifier for our documents, so it's important to have something here even if the message is malformed.
    annotations = payload.get("annotations", {}) # Get the annotations dict or use an empty dict if it's missing. This way we can avoid errors later on when we try to access specific annotation fields.

    print(f"[{SERVICE_NAME}] Received inference results for image: {image_id}")

    # Build the document we want to store in our database. This is where we decide what information to keep and how to structure it.
    # Annotations is a dict that can hold any number of text regions, languages, translations, etc.
    document = {
        "image_id": image_id,
        "path": payload.get("path", ""),
        "source": payload.get("source", ""),
        "detected_text":       annotations.get("detected_text", ""),
        "source_language":     annotations.get("source_language", ""),
        "translation_english": annotations.get("translation_english", ""),
        "confidence_score":    annotations.get("confidence_score", 0.0),
        "status": "stored",
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }

    # insert() silently ignores duplicate image_ids (idempotency)
    inserted = repo.insert(image_id, document)

    # Build and publish annotation.stored regardless of whether it was a duplicate or not
    outgoing_event = create_base_event(
        topic=ANNOTATION_STORED,
        payload={
            "image_id": image_id,
            "path": payload.get("path", ""),
            "source": payload.get("source", ""),
            "inserted": inserted,
            "doc_id": f"doc_{image_id}",
            "detected_text": annotations.get("detected_text", ""),
            "translation_english": annotations.get("translation_english", ""),
        },
    )
    publish_message(ANNOTATION_STORED, outgoing_event)
    print(f"[{SERVICE_NAME}] Published annotation.stored for image: {image_id}")

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    subscribe_to(INFERENCE_COMPLETED, process_event)
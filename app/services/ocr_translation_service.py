

from app.broker import subscribe_to, publish_message
from app.schemas import is_valid_event, create_base_event
from app.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED

# Configuration
SERVICE_NAME = "OCR & Translation Service"
TOPIC_IN = IMAGE_SUBMITTED  # This is the topic we listen to for new images
TOPIC_OUT = INFERENCE_COMPLETED  # This is the topic we publish our OCR results to

def process_event(event_data: dict):
    """This runs every single time an image is uploaded."""
    
    # Check if the message has the fields we expect. If not, print an error and ignore it.
    if not is_valid_event(event_data):
        print(f"[{SERVICE_NAME}] ERROR: Malformed event received. Dropping message.")
        return 
        
    image_id = event_data["payload"].get("image_id", "unknown")
    path = event_data["payload"].get("path", "")
    print(f"[{SERVICE_NAME}] Received image: {image_id}. Processing...")

    # Stubbed OCR — derives text from the filename so different images get
    # different annotations. Real OCR (e.g. pytesseract) would replace this.
    filename = path.split("/")[-1].lower()
    if "stop" in filename:
        detected_text, source_language, translation_english = "Arrêt", "fr", "Stop"
    elif "yield" in filename:
        detected_text, source_language, translation_english = "Cédez", "fr", "Yield"
    elif "exit" in filename:
        detected_text, source_language, translation_english = "Sortie", "fr", "Exit"
    elif "parking" in filename:
        detected_text, source_language, translation_english = "Stationnement", "fr", "Parking"
    else:
        detected_text, source_language, translation_english = "Inconnu", "fr", "Unknown"

    print(f"[{SERVICE_NAME}] Extracting text... Found: '{detected_text}'")
    print(f"[{SERVICE_NAME}] Translating {source_language} to English... Result: '{translation_english}'")
    
    # Create a new event with the same base information but add our new annotations to the payload
    new_event = create_base_event(
        topic=TOPIC_OUT,
        payload={
            "image_id": image_id,
            "path": event_data["payload"].get("path", ""),
            "source": event_data["payload"].get("source", ""),
            "annotations": {
                "detected_text": detected_text,
                "source_language": source_language,
                "translation_english": translation_english,
                "confidence_score": 0.98,
            },
        },
    )
    
    # Publish the new event to Redis so other services can use it
    publish_message(TOPIC_OUT, new_event)

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    # Start listening to Redis forever
    subscribe_to(TOPIC_IN, process_event)
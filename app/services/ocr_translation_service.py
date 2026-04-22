import sys
import os

# Let Python find the 'app' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

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
    print(f"[{SERVICE_NAME}] Received image: {image_id}. Processing...")
    
    # 2. PLACEHOLDER AI WORK (for now)
    print(f"[{SERVICE_NAME}] Extracting text... Found: 'Arrêt'")
    print(f"[{SERVICE_NAME}] Translating French to English... Result: 'Stop'")
    
    # Create a new event with the same base information but add our new annotations to the payload
    new_event = create_base_event(
        topic=TOPIC_OUT, 
        image_id=image_id, 
        path=event_data["payload"].get("path", ""),
        source=event_data["payload"].get("source", "")
    )
    
    # Add the OCR and translation results to the payload under a new "annotations" field
    new_event["payload"]["annotations"] = {
        "detected_text": "Arrêt",
        "source_language": "fr",
        "translation_english": "Stop",
        "confidence_score": 0.98 # This is a made-up confidence score for demonstration. In a real system, the OCR/translation model would provide this.
    }
    
    # Publish the new event to Redis so other services can use it
    publish_message(TOPIC_OUT, new_event)

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    # Start listening to Redis forever
    subscribe_to(TOPIC_IN, process_event)
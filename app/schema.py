import uuid
from datetime import datetime

def create_base_event(topic: str, image_id: str, path: str, source: str) -> dict:
    """
    This is a helper function.
    Instead of typing out everything every time we want to send a message, we just call this function.
    
    It ensures every message has the required fields: topic, event_id, timestamp, and payload.
    """
    return {
        "type": "event",
        "topic": topic,
        
        # uuid.uuid4() generates a random, unique ID (like '123e4567-e89b-12d3...').
        # This is important to know if any message accidentally get received more than once.
        "event_id": str(uuid.uuid4()), 
        
        # This automatically stamps the message with the current date and time
        "timestamp": datetime.utcnow().isoformat(), 
        
        # The payload holds the actual data about the image
        "payload": {
            "image_id": image_id,
            "path": path,
            "source": source
        }
    }
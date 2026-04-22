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
    
def is_valid_event(event):
    
    #check if the event is a dictionary, if not return 
    if not isinstance(event, dict):
       return False
   
    #need to valid if all fields are in event if not then return
    required = ["topic", "event_id", "timestamp", "payload"]
    for field in required:
        if field not in event:
            return False
        
    #check if the values in event are valid, topic, event_id and timestamp must be strings   
    str_required = ["topic", "event_id", "timestamp"]   
    for field in str_required:
        if not isinstance(event[field], str) or event[field] == "": 
            return False
    #payload must be a dict
    if not isinstance(event["payload"], dict):
        return False
    #if everything checks out then return True
    return True
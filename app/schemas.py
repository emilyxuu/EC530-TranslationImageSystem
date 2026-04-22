import uuid
from datetime import datetime, timezone

def create_base_event(topic: str, payload: dict) -> dict:
    """
    Build a valid event with a generic payload.

    Every event has the four required fields (topic, event_id, timestamp,
    payload). The payload itself is topic-specific — image events carry
    image_id/path/source, query events carry query_id/text/top_k, etc.
    """
    return {
        "type": "event",
        "topic": topic,
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
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
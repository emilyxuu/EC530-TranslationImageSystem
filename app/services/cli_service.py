import argparse
import json
import time
import uuid

from app.broker import redis_client, publish_message
from app.schemas import create_base_event
from app.topics import IMAGE_SUBMITTED, QUERY_SUBMITTED, QUERY_COMPLETED

# How long cmd_search waits for query.completed before giving up
QUERY_TIMEOUT_SECONDS = 10

def cmd_upload(path, source="cli"):
    """Publish an image.submitted event for the given path."""
    
    # Generate a unique image_id. uuid.uuid4().hex gives a long string;
    # [:8] trims it to 8 characters so it's readable.
    image_id = f"img_{uuid.uuid4().hex[:8]}"
    
    # build the event with create_base_event
    event = create_base_event(
        topic=IMAGE_SUBMITTED,
        payload={
            "image_id": image_id,
            "path": path,
            "source": source,
        },
    )  
    
    #  publish the event with publish_message
    publish_message(event["topic"], event)
    
    print(f"Uploaded: {path} (image_id={image_id})")
    return image_id
import json
import random
import time
from pathlib import Path

from app.schemas import create_base_event
from app.topics import IMAGE_SUBMITTED


class EventGenerator:
    def __init__(self, publisher, seed=None):
        # Store the publisher function so other methods can call it
        self._publisher = publisher
        
        # Create a local random number generator seeded with `seed`
        # This keeps our randomness isolated from the rest of the program
        self._rng = random.Random(seed)
        
        # Track every event we publish — useful for debugging and demos
        self.published_events = []
        
    #every method ends up calling this function to send a event out  
    def publish(self, topic, event):
        
        self._publisher(topic, event)
        
        self.published_events.append(event)
    
    #builds a valid image.submitted event, wrapper for create_base_event from schemas.py
    def generate_image_submitted(self, image_id=None, path=None, source="generator"):
        # if image_id is None, generate one using self._rng
        if image_id is None:
            image_id = f"img_{self._rng.randint(1000, 9999)}"
        
        # if path is None, build one from image_id
        if path is None:
            path = f"images/{image_id}.jpg"
        
        #return create_base_event with topic=IMAGE_SUBMITTED
        #       and a payload dict containing image_id, path, and source
        return create_base_event(
            topic = IMAGE_SUBMITTED,
            payload = {
                "image_id" : image_id,
                "path" : path,
                "source" : source,
            },
        )
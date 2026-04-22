
import time


from app.broker import publish_message
from app.schemas import create_base_event
from app.topics import IMAGE_SUBMITTED

# The topic I want to shout my message to
TOPIC_OUT = IMAGE_SUBMITTED # This is the topic that the OCR & Translation Service listens to for new images

def simulate_upload():
    """Pretends a user uploaded a photo from their phone."""
    print("📸 Simulating a user uploading an image of a French stop sign...")
    
    # Create the event using my strict schema rules
    new_event = create_base_event(
        topic=TOPIC_OUT,
        payload={
            "image_id": "sign_001",
            "path": "/uploads/french_stop_sign.jpg",
            "source": "mobile_app",
        },
    )
    
    # Publish it to Redis!
    publish_message(TOPIC_OUT, new_event)
    print("Upload complete. Message sent to the broker!")

if __name__ == "__main__":
    # Wait a couple of seconds just to make reading the terminal easier
    time.sleep(2)
    simulate_upload()
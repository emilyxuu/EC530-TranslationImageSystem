# app/broker.py
import json
import redis

# CONNECT TO REDIS
# This line connects my Python code to the Redis server running on my computer.
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def publish_message(topic: str, message_dict: dict):
    """
    Takes a Python dictionary, turns it into text (JSON), and sends it to a specific topic.
    """
    try:
        # Computers send data over networks as text. 
        # json.dumps() converts our Python dictionary into a text string.
        json_data = json.dumps(message_dict)
        
        # Publish it to Redis
        redis_client.publish(topic, json_data)
        
        # Print a success message to the terminal so we know it worked
        print(f"Published message to '{topic}'!")
        
    except Exception as e:
        # If something breaks, print the error instead of crashing the whole program
        print(f"Failed to publish: {e}")

def subscribe_to(topic: str, callback_function):
    """
    When a message arrives, it hands the message to the 'callback_function' to do some work.
    """
    # Create a pubsub object
    pubsub = redis_client.pubsub()
    
    # Tune the radio to the specific topic we want
    pubsub.subscribe(topic)
    
    print(f"Listening for messages on '{topic}'...")
    
    # This is an infinite loop. It will just sit here and wait for messages.
    for message in pubsub.listen():
        
        # Redis sends some behind-the-scenes setup messages first. 
        # We only care about actual 'message' types.
        if message['type'] == 'message':
            
            # Turn the text string back into a Python dictionary
            data = json.loads(message['data'])
            
            # Give the dictionary to the function that asked to listen
            callback_function(data)
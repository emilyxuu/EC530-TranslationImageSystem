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

def cmd_search(query_text, top_k=5):
    """Publish query.submitted and wait for the matching query.completed."""
    
    # Make a unique ID so we can tell our response apart from anyone else's
    query_id = f"q_{uuid.uuid4().hex[:8]}"
    
    # Subscribe BEFORE publishing — otherwise we could miss the response
    pubsub = redis_client.pubsub()
    pubsub.subscribe(QUERY_COMPLETED)
    
    # build the query.submitted event with create_base_event
   
    event = create_base_event(
        topic=QUERY_SUBMITTED,
        payload={
            "query_id": query_id,
            "text": query_text,
            "top_k": top_k,
        },
    )  
    
    # publish the event with publish_message
    
    publish_message(event["topic"], event)
    
    print(f"Searching for: '{query_text}' (query_id={query_id})")
    
    # Calculate when we should give up
    deadline = time.time() + QUERY_TIMEOUT_SECONDS
    
    # Loop until we get our response or the deadline passes
    while time.time() < deadline:
        # Wait up to 1 second for a message
        message = pubsub.get_message(timeout=1.0)
        
        # Skip Redis setup messages and None (nothing arrived)
        if message is None or message["type"] != "message":
            continue
        
        # Try to decode the JSON. If it fails, skip it (slide 10 robustness).
        try:
            response = json.loads(message["data"])
        except json.JSONDecodeError:
            continue
        
        # Is this response for OUR query? Check the query_id inside the payload.
        response_query_id = response.get("payload", {}).get("query_id")
        if response_query_id != query_id:
            continue
        
        # Found our response. Print results.
        results = response["payload"].get("results", [])
        print(f"\nFound {len(results)} result(s):")
        for i, hit in enumerate(results, 1):
            print(f"  {i}. {hit.get('image_id')}: "
                  f"{hit.get('detected_text')!r} -> {hit.get('translation_english')!r}")
        
        pubsub.close()
        return results
    
    # If we got here, we timed out
    pubsub.close()
    print(f"No response received within {QUERY_TIMEOUT_SECONDS}s. Is the Query Service running?")
    return None


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli_service",
        description="EC530 Image Annotation & Retrieval CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # upload subcommand
    p_upload = subparsers.add_parser("upload", help="Upload an image for processing")
    p_upload.add_argument("path", help="Path to the image file")
    p_upload.add_argument("--source", default="cli", help="Source label (default: cli)")
    
    # search subcommand
    p_search = subparsers.add_parser("search", help="Search stored images by text")
    p_search.add_argument("query", help="Text to search for")
    p_search.add_argument("--top-k", type=int, default=5, help="Max results (default: 5)")
    
    return parser
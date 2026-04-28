from app.broker import subscribe_to, publish_message
from app.schemas import create_base_event, is_valid_event
from app.topics import QUERY_SUBMITTED, QUERY_COMPLETED, ANNOTATION_STORED
import threading
SERVICE_NAME = "Query Service"
# Local view of documents, built from annotation.stored events.
# This is proper event-sourcing — the Query Service doesn't share memory
# with the Document DB service; it subscribes to annotation.stored and
# keeps its own copy.
_local_store = {}

def handle_annotation_stored(event_data):
    """Subscriber: add new documents to our local view."""
    if not is_valid_event(event_data):
        return
    payload = event_data["payload"]
    image_id = payload.get("image_id")
    if image_id:
        _local_store[image_id] = payload
        print(f"[{SERVICE_NAME}] Indexed document for {image_id}")
        
def search_documents(query_text, top_k=5):
    """
    Stub search: return documents whose detected_text or translation_english
    contains the query (case-insensitive).
    
    Week 2 replaces this with FAISS vector similarity. The function signature
    stays the same so callers don't change.
    """
    # Lowercase the query once so we can compare case-insensitively
    query_lower = query_text.lower()
    
    matches = []
    
    # loop through every document in document_db_service.repo
 
    for image_id, doc in _local_store.items():
        detected = doc.get("detected_text", "").lower()
        translated = doc.get("translation_english", "").lower()
        if query_lower in detected or query_lower in translated:
            matches.append({
                "image_id": image_id,
                "detected_text": doc.get("detected_text", ""),
                "translation_english": doc.get("translation_english", ""),
                "score": 1.0,
            })
    
    # return the first top_k matches
   
    return matches[:top_k]

def process_event(event_data):
    """Handle a query.submitted event and publish query.completed."""
    
    #reject malformed events with is_valid_event
   
    if not is_valid_event(event_data):
        return
    
    # Pull the query details out of the payload
    payload = event_data["payload"]
    query_id = payload.get("query_id", "unknown")
    query_text = payload.get("text", "")
    top_k = payload.get("top_k", 5)
    
    print(f"[{SERVICE_NAME}] Received query '{query_text}' (query_id={query_id})")
    
    #call search_documents(query_text, top_k) and store the result in `results`
    results = search_documents(query_text, top_k)
    
    #build the response event with create_base_event
   
    response = create_base_event(
        topic=QUERY_COMPLETED,
        payload={
            "query_id": query_id,
            "text": query_text,
            "results": results,
            "result_count": len(results),
        },
    )
    
    
    #  publish the response with publish_message
    publish_message(QUERY_COMPLETED, response)
    
    print(f"[{SERVICE_NAME}] Published query.completed with {len(results)} result(s)")
    

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")

    # Thread 1: listen for annotation.stored to build the local index
    t = threading.Thread(
        target=subscribe_to,
        args=(ANNOTATION_STORED, handle_annotation_stored),
        daemon=True,
    )
    t.start()

    # Main thread: listen for query.submitted
    subscribe_to(QUERY_SUBMITTED, process_event)
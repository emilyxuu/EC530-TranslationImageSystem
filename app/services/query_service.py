from app.broker import subscribe_to, publish_message
from app.schemas import create_base_event, is_valid_event
from app.topics import QUERY_SUBMITTED, QUERY_COMPLETED
from app.services import document_db_service

SERVICE_NAME = "Query Service"

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
 
    for image_id, doc in document_db_service.repo.all().items():
    
        # inside the loop, get detected_text and translation_english from doc
        #       (both lowercased for comparison)
      
        
        detected_text = doc.get("detected_text", "").lower()
        translation_english = doc.get("translation_english", "").lower()
        # check if query_lower is IN either string
        #       If yes, append a result dict
    
        if query_lower in detected_text or query_lower in translation_english:
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
    subscribe_to(QUERY_SUBMITTED, process_event)
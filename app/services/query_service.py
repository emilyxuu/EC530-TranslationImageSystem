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
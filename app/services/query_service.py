import json
import threading
from pathlib import Path

import faiss
import numpy as np

from app.broker import subscribe_to, publish_message
from app.schemas import create_base_event, is_valid_event
from app.topics import (
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
    ANNOTATION_STORED,
    EMBEDDING_CREATED,
)

SERVICE_NAME = "Query Service"


# Path to the dataset — needed for the label_embeddings used to convert
# search queries into vectors.
DATASET_PATH = Path("app/sample_data/embeddings.json")

# Local view of documents, built from annotation.stored events.
_local_store = {}


# Load label embeddings at startup so we can map "stop" → query vector.
with open(DATASET_PATH) as f:
    _label_embeddings = json.load(f)["label_embeddings"]
print(f"[{SERVICE_NAME}] Loaded {len(_label_embeddings)} label embeddings")
# Local view of the vector index, built from embedding.created events.
EMBEDDING_DIM = 8
_vector_index = faiss.IndexFlatIP(EMBEDDING_DIM)
_position_to_image_id = []
_image_id_to_position = {}

def _add_to_index(image_id, embedding):
    """Add one (image_id, vector) pair to the FAISS index."""
    if image_id in _image_id_to_position:
        return
    vector = np.array([embedding], dtype="float32")
    faiss.normalize_L2(vector)
    position = _vector_index.ntotal
    _vector_index.add(vector)
    _position_to_image_id.append(image_id)
    _image_id_to_position[image_id] = position
    
def handle_embedding_created(event_data):
    if not is_valid_event(event_data):
        return
    payload = event_data["payload"]
    image_id = payload.get("image_id")
    embedding = payload.get("embedding")
    if not image_id or not embedding:
        return
    _add_to_index(image_id, embedding)
    print(f"[{SERVICE_NAME}] Indexed vector for {image_id} (index size: {_vector_index.ntotal})")



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
    Vector similarity search.
    
    Steps:
      1. Convert the user's query text into a query vector by looking up
         the matching label in _label_embeddings.
      2. Compute cosine similarity between the query vector and every
         stored image vector in _vector_index.
      3. Return the top_k matches, enriched with document fields from _local_store.
    """
    query_lower = query_text.lower()
    
    # find the query vector by checking each label in _label_embeddings.
    #       Match if the label appears in query_lower (substring match).
    #       If no label matches, return [] (no results).
    #       Hint: for label, vector in _label_embeddings.items(): ...
    query_vector = None
    for label, vector in _label_embeddings.items():
        if label in query_lower:
            query_vector = vector
            break
    
    if query_vector is None:
        print(f"[{SERVICE_NAME}] No matching label for query '{query_text}'")
        return []
    
    # compute similarity for every (image_id, stored_vector) in _vector_index.
    #       Append a dict to `matches` with image_id and score.
    # Empty index? Return empty results.
    if _vector_index.ntotal == 0:
        return []

    query = np.array([query_vector], dtype="float32")
    faiss.normalize_L2(query)

    k = min(top_k, _vector_index.ntotal)
    scores, positions = _vector_index.search(query, k=k)

    matches = []
    for score, position in zip(scores[0], positions[0]):
        if position == -1:
            continue
        image_id = _position_to_image_id[position]
        matches.append({"image_id": image_id, "score": float(score)})
    
    # Enrich results with detected_text and translation_english from _local_store
    # so the CLI can display them. _local_store may not have every image_id
    # (events can arrive out of order), so use .get() with empty fallback.
    for m in matches:
        doc = _local_store.get(m["image_id"], {})
        m["detected_text"] = doc.get("detected_text", "")
        m["translation_english"] = doc.get("translation_english", "")
    
    return matches

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

    # Thread 1: listen for annotation.stored to build the local document store
    t1 = threading.Thread(
        target=subscribe_to,
        args=(ANNOTATION_STORED, handle_annotation_stored),
        daemon=True,
    )
    t1.start()

    # Thread 2: listen for embedding.created to build the local vector index
    t2 = threading.Thread(
        target=subscribe_to,
        args=(EMBEDDING_CREATED, handle_embedding_created),
        daemon=True,
    )
    t2.start()

    # Main thread: listen for query.submitted (this is what the CLI sends)
    subscribe_to(QUERY_SUBMITTED, process_event)
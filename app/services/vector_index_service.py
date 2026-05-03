import faiss
import numpy as np

from app.broker import subscribe_to
from app.schemas import is_valid_event
from app.topics import EMBEDDING_CREATED

SERVICE_NAME = "Vector Index Service"

# Vector dimensionality — 
EMBEDDING_DIM = 512

# FAISS index. IndexFlatIP = inner product (= cosine on normalized vectors).
_index = faiss.IndexFlatIP(EMBEDDING_DIM)

# FAISS uses integer positions for vectors. We need a parallel mapping
# back to image_ids so search results can be reported by image_id.
_position_to_image_id = []   # list: position → image_id
_image_id_to_position = {}   # dict: image_id → position (used for dedup)

def _add_to_index(image_id, embedding):
    """Add one (image_id, vector) pair to the FAISS index."""
    
    # Idempotency: skip if we already indexed this image_id
    if image_id in _image_id_to_position:
        return
    
    # FAISS needs a numpy array shaped (1, dim) of float32
    vector = np.array([embedding], dtype="float32")
    
    # Normalize so that inner product equals cosine similarity
    faiss.normalize_L2(vector)
    
    # The position assigned by FAISS = current index size BEFORE adding
    position = _index.ntotal
    
    _index.add(vector)
    
    # Update the mappings so we can map the position back later
    _position_to_image_id.append(image_id)
    _image_id_to_position[image_id] = position



def search_similar(query_vector, top_k=5):
    """Find the top_k stored vectors most similar to query_vector."""
    
    # Empty index? Return empty results.
    if _index.ntotal == 0:
        return []
    
    # convert query_vector (a Python list) into a numpy float32 array
    #       shaped (1, dim) — same shape as in _add_to_index

    query = np.array([query_vector], dtype="float32")
    
    #normalize the query vector with faiss.normalize_L2()
    
    faiss.normalize_L2(query)
    # FAISS search. Don't ask for more results than we have.
    k = min(top_k, _index.ntotal)
    scores, positions = _index.search(query, k=k)
    
    # scores and positions are 2D arrays; we only made one query so take row 0
    matches = []
    for score, position in zip(scores[0], positions[0]):
        # FAISS returns -1 for "no result" if k > ntotal
        if position == -1:
            continue
        image_id = _position_to_image_id[position]
        matches.append({
            "image_id": image_id,
            "score": float(score),   # convert numpy float to Python float
        })
    
    return matches
    
def handle_embedding_created(event_data):
    """Subscriber: when a new embedding arrives, add it to the FAISS index."""
    if not is_valid_event(event_data):
        return
    
    payload = event_data["payload"]
    image_id = payload.get("image_id")
    embedding = payload.get("embedding")
    
    if not image_id or not embedding:
        return
    
    _add_to_index(image_id, embedding)
    print(f"[{SERVICE_NAME}] Indexed embedding for {image_id} (index size: {_index.ntotal})")
    
       
if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    subscribe_to(EMBEDDING_CREATED, handle_embedding_created)
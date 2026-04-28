import math

from app.broker import subscribe_to
from app.schemas import is_valid_event
from app.topics import EMBEDDING_CREATED

SERVICE_NAME = "Vector Index Service"

# In-memory vector index: {image_id: vector}
# Built up from embedding.created events as they arrive.
_index = {}

def _dot_product(a, b):
    """Sum of element-wise products: a[0]*b[0] + a[1]*b[1] + ..."""
    # use sum() with a generator expression that multiplies pairs from zip(a, b)
    #       Hint: sum(x * y for x, y in zip(a, b))
    return sum(x * y for x, y in zip(a, b))

def _norm(v):
    """Vector length (Euclidean norm): sqrt(v[0]**2 + v[1]**2 + ...)"""
    # sum the squares of every element, then take the square root
    #       Hint: sum(x * x for x in v) gives the sum of squares
    #             math.sqrt(...) gives the square root
    c = sum(x * x for x in v)
    return math.sqrt(c)

def _cosine_similarity(a, b):
    """
    How aligned are vectors a and b in direction?
    Returns 1.0 (identical direction), 0.0 (perpendicular), -1.0 (opposite).
    
    Formula: dot(a, b) / (norm(a) * norm(b))
    """
    # Edge case: if either vector is all zeros, norm is 0 and we'd divide by zero.
    # Return 0 in that case (no meaningful similarity).
    norm_a = _norm(a)
    norm_b = _norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # return _dot_product(a, b) divided by (norm_a * norm_b)
    dot_prod = _dot_product(a,b)
    mult_a_b = norm_a * norm_b
    
    return dot_prod / mult_a_b

def search_similar(query_vector, top_k=5):
    """
    Find the top_k stored vectors most similar to query_vector.
    
    Returns a list of dicts with image_id and score, sorted highest score first.
    """
    matches = []
    
    # loop through every image_id and stored_vector in _index
    
    for image_id, stored_vector in _index.items():
        key = _cosine_similarity(query_vector, stored_vector)
        matches.append({"image_id": image_id, "score": key})

    
    matches.sort(key=lambda m: m["score"], reverse=True)
    
    return matches[:top_k]
    
def handle_embedding_created(event_data):
    """Subscriber: when a new embedding arrives, add it to the index."""
    
    # reject malformed events with is_valid_event (return early if invalid)
    if not is_valid_event(event_data):
        return
    
    payload = event_data["payload"]
    image_id = payload.get("image_id")
    embedding = payload.get("embedding")
    
    # Defensive check: only index if we have both an image_id and an embedding
    if not image_id or not embedding:
        return
    
    _index[image_id] = embedding
    print(f"[{SERVICE_NAME}] Indexed embedding for {image_id} (index size: {len(_index)})")
    
    
    
if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME}...")
    subscribe_to(EMBEDDING_CREATED, handle_embedding_created)
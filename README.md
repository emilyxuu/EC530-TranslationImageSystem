# EC530 Project 2
## Event-Driven Image Annotation and Retrieval System

An event-driven, microservice-based image processing pipeline. Images flow through stubbed OCR/translation, get stored as flexible documents in MongoDB, are encoded into 512-dim vectors using CLIP, and are searchable via natural-language queries through FAISS-based vector similarity.

The original inspiration was helping people with language barriers — a system that could read foreign road signs and produce instant English translations. The architecture is genuinely useful for any "search images by what they're about" application.

## What this project demonstrates

- **Event-driven microservices** — six independent processes coordinating only through Redis pub-sub. No service reaches into another service's memory or database.
- **Real document database** — MongoDB stores annotation records with idempotency at the repository layer.
- **Real vector search** — FAISS index with cosine similarity (via inner product on normalized vectors).
- **Real semantic embeddings** — CLIP (`clip-ViT-B-32`) produces 512-dim image and text embeddings in a shared space.
- **System guarantees from slide 10** — idempotency, robustness, eventual consistency, accurate queries — each implemented and demonstrable.

## Architecture
The Query Service maintains its own local replicas of the document store and vector index by subscribing to `annotation.stored` and `embedding.created`. This is event sourcing — services share contracts (event schemas), not memory.

See `docs/topics_and_messages.md` for the full topic and ownership specification.

## Project Structure
## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

This pulls in Redis client, pymongo, FAISS, sentence-transformers (CLIP), and python-dotenv. First-time install is ~2 GB because of PyTorch.

### 2. Start Redis (in WSL or Docker)

```bash
# WSL
sudo service redis-server start
redis-cli ping  # should return PONG

# Or Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Start MongoDB (in WSL)

```bash
sudo service mongod start
sudo service mongod status  # should show active (running)
```

### 4. Configure environment

```bash
cp .env.example .env
```

For local development the example values work as-is. Update if running Redis/Mongo elsewhere.

### 5. Provide sample images

Place a few image files in `app/sample_data/images/`. The OCR stub keys off filename — names containing `stop`, `yield`, `exit`, or `parking` get matching translations.

## Running the Pipeline

Open a separate terminal for each service (six total). Order matters — start subscribers before publishing.

```bash
# Terminal 1: OCR
python -m app.services.ocr_translation_service

# Terminal 2: Document DB
python -m app.services.document_db_service

# Terminal 3: Embedding (~10s startup for CLIP)
python -m app.services.embedding_service

# Terminal 4: Vector Index
python -m app.services.vector_index_service

# Terminal 5: Query (~10s startup for CLIP)
python -m app.services.query_service

# Terminal 6: CLI — upload and search
python -m app.services.cli_service upload app/sample_data/images/Stop_Sign1.jpg
python -m app.services.cli_service upload app/sample_data/images/Yield_Sign1.jpg
python -m app.services.cli_service search "stop sign"
python -m app.services.cli_service search "yield sign"
```

Expected output (with two images uploaded):
$ search "stop sign"

img_xxx (score: 0.293): 'Arrêt' -> 'Stop'      ← stop sign ranks first
img_yyy (score: 0.282): 'Cédez' -> 'Yield'

$ search "yield sign"

img_yyy (score: 0.370): 'Cédez' -> 'Yield'     ← yield sign ranks first
img_xxx (score: 0.270): 'Arrêt' -> 'Stop'


The same two images return in different orders for different queries — that's CLIP encoding actual visual content, not the stubbed OCR text.

## Event Schema

Every event uses the same envelope:

```json
{
  "topic": "image.submitted",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": { ... }
}
```

`is_valid_event()` in `schemas.py` enforces this contract. Every consumer service rejects malformed events at the door before any processing.

## System Guarantees

| Guarantee | Implementation | Tested by |
|---|---|---|
| Idempotency | `DocumentRepository.insert` checks for existing `image_id` before writing. Duplicates publish `annotation.stored` with `inserted: false`. | `EventGenerator.inject_duplicate(event)` |
| Robustness | All consumers call `is_valid_event()` first; malformed events are dropped, not crashed. | `EventGenerator.inject_malformed()` |
| Eventual consistency | Services hold local replicas built from event streams; late events still arrive correctly. | `EventGenerator.inject_delayed()` |
| Accurate queries | Query Service searches its current local indexes; results reflect everything processed so far. | End-to-end integration tests |

## Stubbing decisions

Per slide 4 ("PLEASE don't focus on AI"), several components are intentionally stubbed:

- **OCR**: derived from filename rather than running real OCR on the image. Real OCR (e.g., Tesseract) would be a one-class swap.
- **Translation**: hardcoded mappings per detected text.
- **Image quality**: any RGB image works; no preprocessing or augmentation.

CLIP-based embedding and FAISS-based search are *not* stubbed — they run on real model output and real similarity math.

## Tests

The testing suite utilizes `pytest` to strictly verify the required system guarantees and defensive programming requirements:

* **Schema Contracts:** Ensures all messages strictly adhere to the required event format (`test_schemas.py`).
* **Robustness:** Proves the microservices gracefully drop malformed payloads and missing keys without crashing (`test_malformed_events.py`).
* **Idempotency:** Verifies that injecting duplicate `event_id`s does not create duplicate state in the MongoDB repository (`test_duplicate_events.py`, `test_idempotency.py`).
* **System Integration:** Simulates deterministic event generation and full end-to-end pipeline flow (`test_pipeline_flow.py`, `test_event_generator.py`).

To run the full suite, execute the following from the root directory:
```bash
pytest tests/ -v
```

## LLM Usage

Claude was used as a pair-programmer for structural review, walking through design decisions, and suggesting where boilerplate could be shortened. All logic was implemented by the author.

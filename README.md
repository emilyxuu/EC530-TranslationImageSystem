# EC530 Project 2
## Event-Driven Image Text Recognition and Translation System

## Overview
This project is a modular, event-driven image-processing pipeline. It uses Redis publish-subscribe (pub-sub) messaging to coordinate services asynchronously.
The inspiration of this project topic is to be able to build a system that works to help those with language barriers understand important information, for example, reading a foreign road sign or document and receiving an instant English translation (and help my immigrant parents overcome simple but important language barriers better than my younger self could).

## Project Structure
* `app/topics.py`: All Redis topic name constants (single source of truth).
* `app/config.py`: Redis connection settings.
* `app/broker.py`: The Redis pub-sub wrapper for passing messages.
* `app/schemas.py`: Helper that builds valid event messages.
* `app/repository.py`: In-memory document store with idempotency (MongoDB placeholder).
* `app/event_generator.py`: Generates mocked events deterministically for testing.
* `app/services/`: Contains the microservices.
* `tests/`: Contains the `pytest` suite proving system robustness and idempotency.

```
event-driven-image-system/
│
├── README.md
├── requirements.txt
│
├── docs/
│   └── topics_and_messages.md
│
├── app/
│   ├── main.py                        # Demo runner (no Redis needed)
│   ├── config.py                      # Redis connection settings
│   ├── topics.py                      # All topic name constants
│   ├── schemas.py                     # create_base_event() helper
│   ├── broker.py                      # Redis pub-sub wrapper
│   ├── event_generator.py             # Deterministic test event generator
│   ├── repository.py                  # In-memory document store
│   │
│   ├── services/
│   │   ├── upload_service.py          # Publishes image.submitted
│   │   ├── ocr_translation_service.py # OCR stub → publishes inference.completed
│   │   ├── document_db_service.py     # Stores annotation → publishes annotation.stored
│   │   ├── embedding_service.py       # Stub → publishes embedding.created (Week 2)
│   │   └── vector_index_service.py    # Stub → FAISS vector search (Week 2)
│   │
│   └── sample_data/
│       └── sample_events.json
│
└── tests/
    ├── test_event_schema.py
    ├── test_event_generator.py
    ├── test_upload_service.py
    ├── test_inference_service.py
    ├── test_document_db_service.py
    ├── test_duplicate_events.py
    ├── test_malformed_events.py
    └── test_pipeline_flow.py
```

## Event Pipeline

```
User Uploads Image
      │
      ▼
[Upload Service] ──────────────────────▶ image.submitted
      │
      ▼
[OCR & Translation Service] ───────────▶ inference.completed
  (detects text, identifies language, translates to English)
      │
      ▼
[Document DB Service] ─────────────────▶ annotation.stored
  (stores flexible JSON doc per image)
      │
      ▼
[Embedding Service] ───────────────────▶ embedding.created   ← Week 2
      │
      ▼
[Vector Index Service]                                        ← Week 2
  (FAISS semantic search over extracted text)
```

## Setup & Prerequisites
1. Install dependencies: `pip install -r requirements.txt`
2. Start the Redis broker: `docker-compose up -d`

## Running the Demo (No Redis Needed)
```bash
python -m app.main
```

## Running the Live Pipeline (Redis Required)
Open a separate terminal for each service:
```bash
# Terminal 1: OCR
python -m app.services.ocr_translation_service

# Terminal 2: DocDB
python -m app.services.document_db_service

# Terminal 3: Embedding
python -m app.services.embedding_service

# Terminal 4: Vector Index
python -m app.services.vector_index_service

# Terminal 5: Query
python -m app.services.query_service

sudo service redis-server start
redis-cli ping
## Running Unit Tests
```bash
pytest tests/ -v
```

## LLM Usage
* Every unit test BUT THE FIRST TEST was generated using an LLM.
* Claude was used for code review and overall structural checks.


Todo: 


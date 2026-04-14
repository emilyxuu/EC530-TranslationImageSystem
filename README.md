# EC530 Project 2
## Event-Driven Image Text Recognition and Translation System

## Overview
This project is a modular, event-driven image-processing pipeline. It uses Redis publish-subscribe (pub-sub) messaging to coordinate services asynchronously. The inspiration of this project topic is to be able to build a system that works to help those with language barriers understand important information.

## Project Structure
* `app/broker.py`: The Redis pub-sub wrapper for passing messages.
* `app/event_generator.py`: Generates mocked events deterministically for testing.
* `app/schemas.py`: Defines the required fields each event message must contain.
* `app/services/`: Contains the microservices (Upload, Inference, Document DB, etc.).
* `tests/`: Contains the `pytest` suite proving system robustness and idempotency.

```
event-driven-image-system/
│
├── README.md
├── requirements.txt
├── .env.example
├── docker-compose.yml
│
├── docs/
│   ├── architecture.md
│   └── topics_and_messages.md
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── topics.py
│   ├── schemas.py
│   ├── broker.py
│   ├── event_generator.py
│   ├── repository.py
│   │
│   ├── services/
│   │   ├── upload_service.py
│   │   ├── inference_service.py
│   │   ├── document_db_service.py
│   │   ├── embedding_service.py
│   │   └── vector_index_service.py
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
Services communicate via events and do not bypass the broker.
1. **User Uploads Image** -> `Upload Service` publishes `image.submitted`
2. **OCR & Translation Service** -> Listens to `image.submitted`, extracts/translates text, and publishes `inference.completed`
3. **Document DB Service** -> Listens to `inference.completed`, stores annotations, and publishes `annotation.stored`
4. **Embedding Service** -> Listens to `annotation.stored`, publishes `embedding.created`
5. **Vector Index Service** -> Placeholder for future semantic search.

## Setup & Prerequisites
1. Install dependencies: `pip install -r requirements.txt`
2. Start the Redis broker using Docker: `docker-compose up -d`

## Running the Application (Live Services)
To run the live pipeline, open separate terminals for each service:
* **Terminal 1:** `python -m app.services.inference_service`
* **Terminal 2:** `python -m app.services.document_db_service`
* **Terminal 3:** `python -m app.main`

## Running Unit Tests
The test suite proves system robustness, idempotency, and schema validation. You can run the tests independently of the live services.
Run the following command from the root directory:
`pytest tests/ -v`

## LLM Usage
* Every unit test BUT THE FIRST TEST was generated using an LLM.
* Claude was used for code review and overall structural checks.
# Topics, Messages, and Service Ownership

This document defines the architecture of the Event-Driven Image Annotation
and Retrieval System: which services exist, what data each one owns, every
Redis topic, and who publishes or subscribes to each.

Slide 11 (Project 2 spec) requires this document.

---

## Services

| Service | File | Responsibility | Owns |
|---|---|---|---|
| CLI Service | `app/services/cli_service.py` | User-facing entry point. Publishes uploads and queries; receives query responses. | Nothing — pure I/O. |
| Upload Service | `app/services/upload_service.py` | Demo/simulator that publishes a sample `image.submitted` event. | Nothing. |
| OCR & Translation Service | `app/services/ocr_translation_service.py` | Receives `image.submitted`, runs (stubbed) OCR + translation, publishes `inference.completed`. | Nothing — stateless transformer. |
| Document DB Service | `app/services/document_db_service.py` | Receives `inference.completed`, stores the annotation document, publishes `annotation.stored`. **Sole writer to the document store.** | TinyDB document store at `data/documents.json`. |
| Embedding Service | `app/services/embedding_service.py` | Receives `annotation.stored`, looks up or generates an embedding vector, publishes `embedding.created`. | Read-only access to `app/sample_data/embeddings.json`. |
| Vector Index Service | `app/services/vector_index_service.py` | Receives `embedding.created`, indexes the vector. Provides similarity search over its index. | In-memory vector index `{image_id: vector}`. |
| Query Service | `app/services/query_service.py` | Receives `query.submitted`, performs vector similarity search, publishes `query.completed`. | Local replicas of the document store and vector index, both built from event streams. |

### Ownership rule (Slide 9)

Only the Document DB Service writes to the document store. Only the Vector
Index Service writes to the index. The CLI does not access either store
directly — it goes through the Query Service via pub-sub.

The Query Service maintains *replicas* of both stores by subscribing to
`annotation.stored` and `embedding.created`. This is event sourcing: the
authoritative writers publish, and read-side services build their own
views. In a production system, the Query Service might query the
authoritative stores directly via RPC, but the pub-sub-only architecture
matches the spec's strict ownership model and avoids cross-process memory
sharing.

---

## Topics

All topics are defined in `app/topics.py` as constants. Renaming a topic
requires changing it in exactly one place.

### `image.submitted`

Published when a user (or simulator) submits an image for processing.

```json
{
  "type": "event",
  "topic": "image.submitted",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "image_id": "img_3a93af47",
    "path": "/uploads/french_stop_sign.jpg",
    "source": "cli"
  }
}
```

### `inference.completed`

Published when the OCR + translation step finishes for an image.

```json
{
  "type": "event",
  "topic": "inference.completed",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "image_id": "img_3a93af47",
    "path": "/uploads/french_stop_sign.jpg",
    "source": "cli",
    "annotations": {
      "detected_text": "Arrêt",
      "source_language": "fr",
      "translation_english": "Stop",
      "confidence_score": 0.98
    }
  }
}
```

### `annotation.stored`

Published when the document store has accepted (or rejected as duplicate)
the annotation. Carries forward the OCR fields so downstream services
don't need to call back into the Document DB.

```json
{
  "type": "event",
  "topic": "annotation.stored",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "image_id": "img_3a93af47",
    "path": "/uploads/french_stop_sign.jpg",
    "source": "cli",
    "inserted": true,
    "doc_id": "doc_img_3a93af47",
    "detected_text": "Arrêt",
    "translation_english": "Stop"
  }
}
```

The `inserted` flag is `false` when the event is a duplicate — downstream
services use this to know whether to re-process or skip.

### `embedding.created`

Published when an embedding has been generated for an image.

```json
{
  "type": "event",
  "topic": "embedding.created",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "image_id": "img_3a93af47",
    "embedding": [0.95, 0.10, 0.20, 0.00, 0.00, 0.00, 0.90, 0.00],
    "dim": 8
  }
}
```

### `query.submitted`

Published by the CLI when the user runs a search.

```json
{
  "type": "event",
  "topic": "query.submitted",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "query_id": "q_5190f633",
    "text": "stop",
    "top_k": 5
  }
}
```

### `query.completed`

Published by the Query Service in response to a `query.submitted`.

```json
{
  "type": "event",
  "topic": "query.completed",
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601 UTC>",
  "payload": {
    "query_id": "q_5190f633",
    "text": "stop",
    "results": [
      {
        "image_id": "sign_001",
        "score": 0.97,
        "detected_text": "Arrêt",
        "translation_english": "Stop"
      }
    ],
    "result_count": 1
  }
}
```

The CLI matches `query_id` to its own outgoing query so multiple CLIs
sharing the topic don't pick up each other's responses.

---

## Pub/Sub Matrix

| Topic | Publishers | Subscribers |
|---|---|---|
| `image.submitted` | CLI Service, Upload Service, Event Generator | OCR & Translation Service |
| `inference.completed` | OCR & Translation Service | Document DB Service |
| `annotation.stored` | Document DB Service | Embedding Service, Query Service |
| `embedding.created` | Embedding Service | Vector Index Service, Query Service |
| `query.submitted` | CLI Service | Query Service |
| `query.completed` | Query Service | CLI Service |

---

## Event Envelope Contract

Every event, regardless of topic, has the same four required fields:
`topic`, `event_id`, `timestamp`, `payload`. The validator
`is_valid_event()` in `app/schemas.py` enforces this. Per-topic payload
shape is enforced by convention — each consumer pulls the fields it needs
with `.get()` and ignores anything else.

This contract is the only formal interface between services. As long as
events conform, services can be modified or replaced independently.

---

## System Guarantees (Slide 10)

| Guarantee | How it's implemented | Test strategy |
|---|---|---|
| Idempotency | Document DB Service's `insert` checks for existing `image_id` before writing. Duplicate events publish `annotation.stored` with `inserted: false`. | `EventGenerator.inject_duplicate(event)` re-publishes an event; the document store remains at one record. |
| Robustness | Every consumer calls `is_valid_event()` first and drops malformed events without crashing. | `EventGenerator.inject_malformed()` publishes a broken event; the consumer prints an error and continues. |
| Eventual consistency | Services hold local replicas built from event streams. Late or out-of-order events still update the local state correctly because handlers are idempotent on `image_id`. | `EventGenerator.inject_delayed(event, seconds)` publishes after a delay; the system converges once the event arrives. |
| Accurate queries | The Query Service returns results based on its current local index. Searches reflect everything that's been processed up to that moment. | Run uploads, then a query, and verify the results contain only the uploads' image_ids. |
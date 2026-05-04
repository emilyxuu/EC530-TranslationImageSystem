import pytest
import app.services.document_db_service as db_service
from app.event_generator import EventGenerator

def test_db_publishes_annotation_stored(monkeypatch, test_repo):
    """Proves the DB service successfully saves and publishes annotation.stored."""
    # Point the service to our safe test database
    monkeypatch.setattr(db_service, "repo", test_repo)
    
    published_events = []
    monkeypatch.setattr(db_service, "publish_message", lambda topic, event: published_events.append(event))
    
    # Create a fake completed inference event
    generator = EventGenerator(publisher=lambda t, e: None, seed=1)
    event = generator.generate_image_submitted()
    event["payload"]["annotations"] = {"detected_text": "Arrêt", "translation_english": "Stop"}
    
    db_service.process_event(event)
    
    assert len(published_events) == 1
    assert published_events[0]["topic"] == "annotation.stored"
    assert published_events[0]["payload"]["inserted"] is True
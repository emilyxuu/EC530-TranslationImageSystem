import pytest
import app.services.document_db_service as db_service
from app.event_generator import EventGenerator

def test_idempotency_prevents_duplicate_records(monkeypatch, test_repo, capsys):
    """Proves that sending the EXACT SAME event twice only inserts into Mongo once."""
    monkeypatch.setattr(db_service, "repo", test_repo)
    monkeypatch.setattr(db_service, "publish_message", lambda topic, event: None)
    
    generator = EventGenerator(publisher=lambda t, e: None, seed=100)
    valid_event = generator.generate_image_submitted(image_id="test_dup_01")
    valid_event["payload"]["annotations"] = {"detected_text": "Test"}
    
    # 1. First Pass
    db_service.process_event(valid_event)
    assert len(test_repo.all()) == 1
    
    # 2. Second Pass (The Duplicate)
    db_service.process_event(valid_event)
    
    # 3. Verify it was blocked
    captured = capsys.readouterr()
    assert len(test_repo.all()) == 1 # Still only 1 record!
    assert "Skipping duplicate" in captured.out
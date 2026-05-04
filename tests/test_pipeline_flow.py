import pytest
from app.event_generator import EventGenerator
import app.services.ocr_translation_service as ocr_service
import app.services.document_db_service as db_service

def test_full_week1_pipeline_flow(monkeypatch, test_repo):
    """Simulates a message flowing from Upload -> OCR -> Database without Redis."""
    monkeypatch.setattr(db_service, "repo", test_repo)
    
    # We will track events as they are "published"
    event_bus = []
    
    # When OCR publishes, send it straight to the DB service
    monkeypatch.setattr(ocr_service, "publish_message", lambda t, e: db_service.process_event(e))
    # When DB publishes, save it to our bus so we can verify it
    monkeypatch.setattr(db_service, "publish_message", lambda t, e: event_bus.append(e))
    
    # 1. Start the flow: Upload a fake yield sign
    generator = EventGenerator(publisher=lambda t, e: None, seed=99)
    upload_event = generator.generate_image_submitted(path="spanish_yield.jpg")
    
    # 2. Trigger the OCR service
    ocr_service.process_event(upload_event)
    
    # 3. Verify the final result made it through the DB
    assert len(event_bus) == 1
    final_event = event_bus[0]
    
    assert final_event["topic"] == "annotation.stored"
    assert final_event["payload"]["inserted"] is True
    assert final_event["payload"]["translation_english"] == "Yield"
    
    # Verify it actually saved in the database
    assert len(test_repo.all()) == 1
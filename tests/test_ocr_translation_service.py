import pytest
from app.services.ocr_translation_service import process_event
from app.event_generator import EventGenerator

def test_ocr_translates_french_stop_sign(monkeypatch):
    """Proves the OCR service detects 'stop' in the path and translates it."""
    # We monkeypatch the publish_message function so it doesn't actually try to connect to Redis
    published_events = []
    import app.services.ocr_translation_service as ocr
    monkeypatch.setattr(ocr, "publish_message", lambda topic, event: published_events.append(event))
    
    # Generate an event where the image path contains 'stop'
    generator = EventGenerator(publisher=lambda t, e: None, seed=1)
    event = generator.generate_image_submitted(path="/uploads/french_stop.jpg")
    
    # Process it
    process_event(event)
    
    # Verify the translation was added
    assert len(published_events) == 1
    annotations = published_events[0]["payload"]["annotations"]
    assert annotations["detected_text"] == "Arrêt"
    assert annotations["translation_english"] == "Stop"
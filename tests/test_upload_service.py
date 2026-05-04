import pytest
import app.services.upload_service as upload_service

def test_upload_publishes_event(monkeypatch):
    """Proves simulating an upload sends an image.submitted message."""
    published_events = []
    # Intercept the publish function so it doesn't need a live Redis server
    monkeypatch.setattr(upload_service, "publish_message", lambda topic, event: published_events.append(event))
    
    upload_service.simulate_upload()
    
    assert len(published_events) == 1
    assert published_events[0]["topic"] == "image.submitted"
    assert published_events[0]["payload"]["source"] == "mobile_app"
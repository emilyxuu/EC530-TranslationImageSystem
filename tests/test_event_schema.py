import pytest
from app.schemas import create_base_event, is_valid_event

def test_valid_event_passes():
    """Proves that a correctly formatted event returns True."""
    event = create_base_event("test.topic", {"some": "data"})
    assert is_valid_event(event) is True

def test_invalid_event_fails():
    """Proves that missing required fields causes validation to fail."""
    bad_event = {
        "type": "event",
        "topic": "test.topic",
        "event_id": "123",
        "timestamp": "2026-05-04"
        # Missing 'payload'
    }
    assert is_valid_event(bad_event) is False

def test_empty_event_fails():
    assert is_valid_event({}) is False
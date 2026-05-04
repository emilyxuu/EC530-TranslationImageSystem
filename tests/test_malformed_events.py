import pytest
from app.event_generator import EventGenerator
from app.services.ocr_translation_service import process_event as ocr_process

def test_robustness_drops_malformed_event(capsys):
    """Injects a malformed event. Proves the service catches it, prints an error, and DOES NOT crash."""
    generator = EventGenerator(publisher=lambda t, e: None, seed=42)
    
    # Generate a broken event (missing payload entirely)
    bad_event = generator.inject_malformed()
    
    # Feed it directly to the OCR service
    ocr_process(bad_event)
    
    # Assert the system handled it gracefully
    captured = capsys.readouterr()
    assert "ERROR: Malformed event" in captured.out
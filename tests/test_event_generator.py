import pytest
from app.event_generator import EventGenerator

def test_deterministic_generation():
    """Proves that providing a seed generates the exact same fake event twice."""
    gen1 = EventGenerator(publisher=lambda t, e: None, seed=42)
    gen2 = EventGenerator(publisher=lambda t, e: None, seed=42)
    
    event1 = gen1.generate_image_submitted()
    event2 = gen2.generate_image_submitted()
    
    assert event1["payload"]["image_id"] == event2["payload"]["image_id"]
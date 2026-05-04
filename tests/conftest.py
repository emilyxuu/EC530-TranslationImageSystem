import pytest
from app.repository import DocumentRepository

@pytest.fixture
def test_repo():
    """Provides a safe test database that gets cleared before and after each test."""
    repo = DocumentRepository(db_name="test_image_annotation_db")
    repo.clear()
    yield repo
    repo.clear()
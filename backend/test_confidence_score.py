import pytest
from app.rag_service import calculate_confidence_score
from app.config import UNANSWERABLE_THRESHOLD

def test_empty_retrieved_items():
    assert calculate_confidence_score([]) == 0.0
    assert calculate_confidence_score(None) == 0.0

def test_no_relevant_items_below_threshold():
    # Items with cosine similarity lower than UNANSWERABLE_THRESHOLD (0.28)
    items = [("chunk1", 0.15), ("chunk2", 0.20), ("chunk3", 0.27)]
    assert calculate_confidence_score(items) == 0.0

def test_single_item_at_threshold():
    items = [("chunk1", 0.28)]
    assert calculate_confidence_score(items) == 0.0

def test_single_item_high_score():
    # Cosine similarity >= 0.80 yields 1.0 (100% confidence)
    items = [("chunk1", 0.82)]
    assert calculate_confidence_score(items) == 1.0

def test_single_item_intermediate_score():
    # Score 0.72: (0.72 - 0.28) / (0.80 - 0.28) = 0.44 / 0.52 = 0.84615 -> 0.8462 (85%)
    items = [("chunk1", 0.72)]
    score = calculate_confidence_score(items)
    assert pytest.approx(score, 0.001) == 0.8462

def test_multiple_relevant_items():
    # Top score 0.54, supporting score 0.40
    # norm(0.54) = (0.54 - 0.28)/0.52 = 0.50
    # norm(0.40) = (0.40 - 0.28)/0.52 = 0.230769
    # aggregated = 0.8 * 0.50 + 0.2 * 0.230769 = 0.40 + 0.0461538 = 0.4462
    items = [("chunk1", 0.54), ("chunk2", 0.40)]
    score = calculate_confidence_score(items)
    assert pytest.approx(score, 0.001) == 0.4462

def test_item_objects_with_similarity_attribute():
    class DummyItem:
        def __init__(self, sim):
            self.similarity_score = sim

    items = [DummyItem(0.72)]
    score = calculate_confidence_score(items)
    assert pytest.approx(score, 0.001) == 0.8462

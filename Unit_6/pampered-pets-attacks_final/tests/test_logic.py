"""Unit tests for the aggregation logic in the attack tree analyzer."""

import math


from app.model import compute_probabilities, expected_loss, top_contributors


def test_and_probability():
    """Probability of an AND node is the product of its children's probabilities."""
    nodes = {
        "n1": {"id": "n1", "type": "AND", "children": ["a", "b"], "label": "", "prob": None, "impact": None},
        "a": {"id": "a", "type": "LEAF", "children": [], "label": "", "prob": 0.5, "impact": 10},
        "b": {"id": "b", "type": "LEAF", "children": [], "label": "", "prob": 0.2, "impact": 5},
    }
    result = compute_probabilities("n1", nodes)
    assert math.isclose(result, 0.1, rel_tol=1e-9)


def test_or_probability():
    """Probability of an OR node is one minus the product of child failure probabilities."""
    nodes = {
        "top": {"id": "top", "type": "OR", "children": ["a", "b"], "label": "", "prob": None, "impact": None},
        "a": {"id": "a", "type": "LEAF", "children": [], "label": "", "prob": 0.3, "impact": 7},
        "b": {"id": "b", "type": "LEAF", "children": [], "label": "", "prob": 0.6, "impact": 2},
    }
    result = compute_probabilities("top", nodes)
    # 1 - (1 - 0.3)*(1 - 0.6) = 1 - 0.7*0.4 = 1 - 0.28 = 0.72
    assert math.isclose(result, 0.72, rel_tol=1e-9)


def test_expected_loss():
    """Expected loss sums probability*impact over all leaves."""
    nodes = {
        "n1": {"id": "n1", "type": "AND", "children": ["a", "b"], "label": "", "prob": None, "impact": None},
        "a": {"id": "a", "type": "LEAF", "children": [], "label": "", "prob": 0.5, "impact": 10},
        "b": {"id": "b", "type": "LEAF", "children": [], "label": "", "prob": 0.2, "impact": 5},
    }
    total = expected_loss(nodes)
    assert math.isclose(total, 0.5 * 10 + 0.2 * 5, rel_tol=1e-9)


def test_top_contributors():
    """Top contributors are sorted by probability*impact."""
    nodes = {
        "a": {"id": "a", "type": "LEAF", "children": [], "label": "A", "prob": 0.1, "impact": 5},
        "b": {"id": "b", "type": "LEAF", "children": [], "label": "B", "prob": 0.4, "impact": 2},
        "c": {"id": "c", "type": "LEAF", "children": [], "label": "C", "prob": 0.2, "impact": 4},
    }
    top = top_contributors(nodes, k=2)
    # contributions: a=0.5, b=0.8, c=0.8. b and c tie; stable sort by order of appearance
    assert len(top) == 2
    # The values should be non‑increasing
    assert top[0]["value"] >= top[1]["value"]
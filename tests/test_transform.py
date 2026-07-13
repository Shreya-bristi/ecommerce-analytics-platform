"""Basic tests for ETL transform logic."""
import pytest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'etl'))


def test_deterministic_variant():
    """Same session + experiment should always return same variant."""
    from transform import deterministic_variant
    v1 = deterministic_variant("session_123", "homepage_v2")
    v2 = deterministic_variant("session_123", "homepage_v2")
    assert v1 == v2, "Variant assignment must be deterministic"
    assert v1 in ("control", "variant")


def test_variant_distribution():
    """Roughly 50/50 split across many sessions."""
    from transform import deterministic_variant
    variants = [
        deterministic_variant(f"session_{i}", "homepage_v2")
        for i in range(10000)
    ]
    control_pct = variants.count("control") / len(variants)
    assert 0.45 < control_pct < 0.55, f"Expected ~50% control, got {control_pct:.2%}"
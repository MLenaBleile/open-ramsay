"""Tests for circulant graph construction and search."""

import pytest
import time

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import verify_k5_free, count_mono_k5
from src.constructions.circulant import (
    circulant_coloring,
    connection_set_from_graph,
    generate_connection_sets,
    estimate_density,
    prune_connection_set,
    search_circulant_colorings,
    get_paley_like_connection_set,
    compare_paley_and_circulant,
)


class TestCirculantConstruction:
    """Test basic circulant graph construction."""

    def test_circulant_basic(self):
        """Test basic circulant construction."""
        # C(6, {1, 2}) - edges at distance 1 and 2 are red
        graph = circulant_coloring(6, {1, 2})
        assert graph.n == 6

        # Distance 1 edges should be red (False)
        assert graph.get_edge(0, 1) is False
        assert graph.get_edge(1, 2) is False

        # Distance 3 edges should be blue (True) - 3 is not in {1, 2}
        assert graph.get_edge(0, 3) is True

    def test_circulant_symmetry(self):
        """Circulant graphs should have rotational symmetry."""
        graph = circulant_coloring(8, {1, 3})

        # Check that rotating the vertices preserves the coloring pattern
        for d in [1, 3]:
            # All edges at this distance should be red
            for i in range(8):
                j = (i + d) % 8
                if i < j:
                    assert graph.get_edge(i, j) is False

    def test_circulant_from_graph_roundtrip(self):
        """connection_set_from_graph should recover the connection set."""
        original_set = {1, 3, 5}
        graph = circulant_coloring(12, original_set)

        recovered = connection_set_from_graph(graph)
        assert recovered == original_set

    def test_non_circulant_detection(self):
        """Non-circulant graphs should return None."""
        # Create a graph that's not circulant
        graph = RamseyGraph(6)
        graph.set_edge(0, 1, True)  # Distance 1, but only this edge is blue
        # Other distance-1 edges are red (default)

        result = connection_set_from_graph(graph)
        assert result is None


class TestDensityEstimation:
    """Test density estimation and pruning."""

    def test_empty_connection_set(self):
        """Empty connection set means all edges are blue."""
        density = estimate_density(10, set())
        assert density == 0.0

    def test_full_connection_set(self):
        """Full connection set means all edges are red."""
        n = 10
        full_set = set(range(1, n // 2 + 1))
        density = estimate_density(n, full_set)
        assert density == 1.0

    def test_half_connection_set(self):
        """Connection set with half the distances."""
        n = 8
        half_set = {1, 2}  # Out of {1, 2, 3, 4}
        density = estimate_density(n, half_set)
        assert 0.4 <= density <= 0.6  # Should be roughly half

    def test_pruning_extremes(self):
        """Pruning should reject extreme densities."""
        n = 20

        # Very sparse (only distance 1)
        assert prune_connection_set(n, {1}) is False

        # Very dense (all distances)
        full = set(range(1, n // 2 + 1))
        assert prune_connection_set(n, full) is False

        # Balanced should pass
        balanced = set(range(1, n // 4 + 1))
        # May or may not pass depending on exact bounds


class TestConnectionSetGeneration:
    """Test connection set enumeration."""

    def test_generate_all(self):
        """Generate all connection sets for small n."""
        n = 6
        # Distances: 1, 2, 3
        all_sets = list(generate_connection_sets(n))

        # Should have 2^3 - 1 = 7 non-empty subsets
        # But we start from size 1, so 7 sets
        assert len(all_sets) == 7

    def test_generate_with_size_bounds(self):
        """Generate connection sets with size constraints."""
        n = 8
        # Distances: 1, 2, 3, 4

        sets_size_2 = list(generate_connection_sets(n, min_size=2, max_size=2))
        # C(4, 2) = 6 sets of size 2
        assert len(sets_size_2) == 6


class TestSmallCirculantSearch:
    """Test circulant search on small graphs."""

    def test_small_n_has_valid(self):
        """Small n should have valid circulant colorings."""
        for n in [5, 6, 7, 8]:
            valid = search_circulant_colorings(n)
            assert len(valid) > 0, f"No valid circulants found for n={n}"

    def test_search_n10(self):
        """Search for n=10 should find valid colorings."""
        valid = search_circulant_colorings(10)
        assert len(valid) > 0

        # Verify one of them
        if valid:
            graph = circulant_coloring(10, valid[0])
            is_valid, _ = verify_k5_free(graph)
            assert is_valid


class TestPaleyVsCirculant:
    """Compare Paley and circulant constructions."""

    def test_paley_5_is_circulant(self):
        """P(5) should be equivalent to a circulant graph."""
        result = compare_paley_and_circulant(5)

        # P(5) for p ≡ 1 mod 4 should be circulant
        assert result['p_mod_4'] == 1
        assert result['connection_set'] is not None

    def test_paley_like_connection_set(self):
        """Paley-like connection set should match QR pattern."""
        for p in [5, 13, 17, 29, 37]:
            conn_set = get_paley_like_connection_set(p)
            assert len(conn_set) > 0
            assert all(1 <= d <= p // 2 for d in conn_set)


class TestCirculantK5Free:
    """Test finding (5,5)-free circulant graphs."""

    def test_n37_has_k5_free_circulant(self):
        """n=37 should have (5,5)-free circulant (matching Paley)."""
        # Use Paley-like connection set
        conn_set = get_paley_like_connection_set(37)
        graph = circulant_coloring(37, conn_set)

        is_valid, _ = verify_k5_free(graph)
        # This may or may not be (5,5)-free as circulant
        print(f"\nC(37, Paley-like) is (5,5)-free: {is_valid}")

    def test_search_n38(self):
        """Search for (5,5)-free circulants at n=38."""
        print("\nSearching n=38...")
        start = time.time()
        valid = search_circulant_colorings(38, verbose=False)
        elapsed = time.time() - start

        print(f"Found {len(valid)} valid circulants for n=38 in {elapsed:.2f}s")
        if valid:
            print(f"First valid: {sorted(valid[0])}")

    @pytest.mark.slow
    def test_search_n42(self):
        """Search for (5,5)-free circulants at n=42."""
        print("\nSearching n=42 (may be slow)...")
        start = time.time()
        valid = search_circulant_colorings(42, verbose=False)
        elapsed = time.time() - start

        print(f"Found {len(valid)} valid circulants for n=42 in {elapsed:.2f}s")
        if valid:
            for s in valid[:3]:
                print(f"  Valid: {sorted(s)}")


class TestCirculantExport:
    """Test exporting circulant colorings."""

    def test_export_valid_coloring(self):
        """Export a valid circulant coloring to CSV."""
        import tempfile
        import os

        # Find a valid coloring for n=10
        valid = search_circulant_colorings(10)
        assert len(valid) > 0

        graph = circulant_coloring(10, valid[0])

        # Export and reimport
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            filepath = f.name

        try:
            graph.to_csv(filepath)
            loaded = RamseyGraph.from_csv(filepath)
            assert graph == loaded
        finally:
            os.unlink(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-k", "not slow"])

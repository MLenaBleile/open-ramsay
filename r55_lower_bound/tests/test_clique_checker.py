"""Tests for clique detection algorithms."""

import pytest
import numpy as np
from itertools import combinations

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import (
    has_mono_k5_brute,
    find_mono_k5_brute,
    count_mono_k5,
    count_mono_k5_total,
    check_edge_flip_delta,
    has_mono_clique,
    count_mono_cliques,
    verify_k5_free,
)
from src.core.utils import binomial


class TestSmallGraphs:
    """Test clique detection on small graphs."""

    def test_k5_all_red_has_red_k5(self):
        """K₅ with all red edges has exactly one red K₅."""
        graph = RamseyGraph(5)  # All edges red by default
        assert has_mono_k5_brute(graph) is True
        red, blue = count_mono_k5(graph)
        assert red == 1
        assert blue == 0

    def test_k5_all_blue_has_blue_k5(self):
        """K₅ with all blue edges has exactly one blue K₅."""
        graph = RamseyGraph(5)
        # Set all edges to blue
        for i in range(5):
            for j in range(i + 1, 5):
                graph.set_edge(i, j, True)

        assert has_mono_k5_brute(graph) is True
        red, blue = count_mono_k5(graph)
        assert red == 0
        assert blue == 1

    def test_k4_has_no_k5(self):
        """K₄ cannot contain a K₅."""
        graph = RamseyGraph(4)
        assert has_mono_k5_brute(graph) is False
        red, blue = count_mono_k5(graph)
        assert red == 0
        assert blue == 0

    def test_k3_has_no_k5(self):
        """K₃ cannot contain a K₅."""
        graph = RamseyGraph(3)
        assert has_mono_k5_brute(graph) is False

    def test_k2_has_no_k5(self):
        """K₂ cannot contain a K₅."""
        graph = RamseyGraph(2)
        assert has_mono_k5_brute(graph) is False


class TestK6:
    """Test K₆ with various colorings."""

    def test_k6_all_red(self):
        """K₆ all red should have C(6,5) = 6 red K₅s."""
        graph = RamseyGraph(6)
        red, blue = count_mono_k5(graph)
        assert red == binomial(6, 5)  # 6
        assert blue == 0

    def test_k6_all_blue(self):
        """K₆ all blue should have 6 blue K₅s."""
        graph = RamseyGraph(6)
        for i in range(6):
            for j in range(i + 1, 6):
                graph.set_edge(i, j, True)

        red, blue = count_mono_k5(graph)
        assert red == 0
        assert blue == 6

    def test_k6_one_blue_edge(self):
        """K₆ with one blue edge reduces red K₅ count appropriately."""
        graph = RamseyGraph(6)  # All red
        # Flip edge (0,1) to blue
        graph.set_edge(0, 1, True)

        # Red K₅s: Any 5-subset NOT containing both 0 and 1
        # 5-subsets not containing 0: C(5,5) = 1 -> {1,2,3,4,5}
        # 5-subsets not containing 1: C(5,5) = 1 -> {0,2,3,4,5}
        # So 2 red K₅s remain
        red, blue = count_mono_k5(graph)
        assert red == 2
        assert blue == 0


class TestFindK5:
    """Test finding specific K₅ subgraphs."""

    def test_find_returns_valid_k5(self):
        """find_mono_k5_brute returns a valid K₅."""
        graph = RamseyGraph(6)  # All red
        result = find_mono_k5_brute(graph)

        assert result is not None
        vertices, color = result
        assert len(vertices) == 5
        assert color is False  # Red

        # Verify it's actually a red K₅
        for i in range(5):
            for j in range(i + 1, 5):
                assert graph.get_edge(vertices[i], vertices[j]) is False

    def test_find_returns_none_when_none_exist(self):
        """find_mono_k5_brute returns None when no K₅ exists."""
        graph = RamseyGraph(4)
        result = find_mono_k5_brute(graph)
        assert result is None


class TestIncrementalChecker:
    """Test incremental K₅ counting for edge flips."""

    def test_flip_creating_k5(self):
        """Flipping an edge to create a K₅ should increase count."""
        # Start with K₅ where one edge is blue
        graph = RamseyGraph(5)
        graph.set_edge(0, 1, True)  # One blue edge

        # Currently no mono-K₅
        assert count_mono_k5_total(graph) == 0

        # Check what happens if we flip (0,1) back to red
        delta = check_edge_flip_delta(graph, (0, 1))
        assert delta == 1  # Would create one red K₅

    def test_flip_destroying_k5(self):
        """Flipping an edge in a K₅ should decrease count."""
        # All red K₅
        graph = RamseyGraph(5)
        assert count_mono_k5_total(graph) == 1

        # Flipping any edge destroys the K₅
        delta = check_edge_flip_delta(graph, (0, 1))
        assert delta == -1  # Would destroy the red K₅

    def test_flip_neutral(self):
        """Some flips don't change K₅ count."""
        # K₆ with exactly edges {0,1} and {2,3} blue
        graph = RamseyGraph(6)
        graph.set_edge(0, 1, True)
        graph.set_edge(2, 3, True)

        # Count current K₅s
        initial_count = count_mono_k5_total(graph)

        # Test flipping edge (0, 2) which connects the two blue edges
        delta = check_edge_flip_delta(graph, (0, 2))

        # Actually flip and verify
        graph.flip_edge(0, 2)
        new_count = count_mono_k5_total(graph)
        assert new_count - initial_count == delta

    def test_delta_matches_full_recount(self):
        """Incremental delta should match full recount."""
        np.random.seed(42)
        graph = RamseyGraph(8)

        # Random coloring
        for i in range(8):
            for j in range(i + 1, 8):
                graph.set_edge(i, j, bool(np.random.randint(2)))

        initial_count = count_mono_k5_total(graph)

        # Test several random edge flips
        for _ in range(10):
            i, j = np.random.randint(8), np.random.randint(8)
            if i >= j:
                continue

            delta = check_edge_flip_delta(graph, (i, j))
            graph.flip_edge(i, j)
            new_count = count_mono_k5_total(graph)

            assert new_count - initial_count == delta, \
                f"Delta {delta} didn't match actual change {new_count - initial_count}"

            initial_count = new_count


class TestGeneralCliques:
    """Test general clique counting (not just K₅)."""

    def test_k3_in_k4(self):
        """K₄ all red has C(4,3) = 4 red K₃s."""
        graph = RamseyGraph(4)
        red, blue = count_mono_cliques(graph, 3)
        assert red == 4
        assert blue == 0

    def test_k4_in_k5(self):
        """K₅ all red has C(5,4) = 5 red K₄s."""
        graph = RamseyGraph(5)
        red, blue = count_mono_cliques(graph, 4)
        assert red == 5
        assert blue == 0

    def test_has_mono_clique_k3(self):
        """Test has_mono_clique for K₃."""
        graph = RamseyGraph(5)  # All red
        assert has_mono_clique(graph, 3, False) is True  # Has red K₃
        assert has_mono_clique(graph, 3, True) is False   # No blue K₃


class TestVerification:
    """Test the verify_k5_free function."""

    def test_valid_graph(self):
        """A K₄ should be verified as K₅-free."""
        graph = RamseyGraph(4)
        is_valid, counterexample = verify_k5_free(graph)
        assert is_valid is True
        assert counterexample is None

    def test_invalid_graph(self):
        """A K₅ all red should fail verification."""
        graph = RamseyGraph(5)
        is_valid, counterexample = verify_k5_free(graph)
        assert is_valid is False
        assert counterexample is not None
        vertices, color = counterexample
        assert len(vertices) == 5
        assert color is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_graph_size(self):
        """Test with minimum valid graph size (n=2)."""
        graph = RamseyGraph(2)
        assert has_mono_k5_brute(graph) is False
        assert count_mono_k5(graph) == (0, 0)

    def test_exactly_k5_size(self):
        """Test with exactly 5 vertices."""
        graph = RamseyGraph(5)
        graph.set_edge(0, 1, True)  # Make it not all-red

        # Still has neither red nor blue K₅
        assert count_mono_k5_total(graph) == 0

        # Make it all blue
        for i in range(5):
            for j in range(i + 1, 5):
                graph.set_edge(i, j, True)

        assert count_mono_k5_total(graph) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for graph construction methods."""

import pytest
import numpy as np

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, has_mono_k5_brute, verify_k5_free
from src.core.utils import edge_index, vertex_pair, num_edges, binomial


class TestUtilityFunctions:
    """Test utility functions."""

    def test_edge_index_and_vertex_pair_inverse(self):
        """edge_index and vertex_pair should be inverses."""
        for n in [5, 10, 20, 44]:
            for i in range(n):
                for j in range(i + 1, n):
                    idx = edge_index(i, j, n)
                    recovered = vertex_pair(idx, n)
                    assert recovered == (i, j), \
                        f"Failed for n={n}, edge=({i},{j}), idx={idx}, recovered={recovered}"

    def test_edge_index_range(self):
        """edge_index should produce valid indices."""
        for n in [5, 10, 20]:
            expected_edges = num_edges(n)
            indices = set()
            for i in range(n):
                for j in range(i + 1, n):
                    idx = edge_index(i, j, n)
                    assert 0 <= idx < expected_edges
                    indices.add(idx)
            assert len(indices) == expected_edges

    def test_num_edges(self):
        """num_edges should compute C(n,2)."""
        assert num_edges(2) == 1
        assert num_edges(3) == 3
        assert num_edges(4) == 6
        assert num_edges(5) == 10
        assert num_edges(44) == 946

    def test_binomial(self):
        """binomial should compute correct values."""
        assert binomial(5, 2) == 10
        assert binomial(44, 5) == 1086008
        assert binomial(10, 0) == 1
        assert binomial(10, 10) == 1
        assert binomial(5, 6) == 0


class TestRamseyGraphConstruction:
    """Test RamseyGraph construction and basic operations."""

    def test_default_all_red(self):
        """Default graph should have all red edges."""
        graph = RamseyGraph(5)
        for i in range(5):
            for j in range(i + 1, 5):
                assert graph.get_edge(i, j) is False

    def test_set_and_get_edge(self):
        """set_edge and get_edge should work correctly."""
        graph = RamseyGraph(5)
        graph.set_edge(0, 1, True)
        assert graph.get_edge(0, 1) is True
        assert graph.get_edge(1, 0) is True  # Symmetric

        graph.set_edge(2, 4, True)
        assert graph.get_edge(4, 2) is True

    def test_flip_edge(self):
        """flip_edge should toggle edge color."""
        graph = RamseyGraph(5)
        assert graph.get_edge(0, 1) is False

        graph.flip_edge(0, 1)
        assert graph.get_edge(0, 1) is True

        graph.flip_edge(1, 0)  # Order shouldn't matter
        assert graph.get_edge(0, 1) is False

    def test_matrix_roundtrip(self):
        """to_matrix and from_matrix should be inverses."""
        graph = RamseyGraph(6)
        np.random.seed(42)
        for i in range(6):
            for j in range(i + 1, 6):
                graph.set_edge(i, j, bool(np.random.randint(2)))

        matrix = graph.to_matrix()
        recovered = RamseyGraph.from_matrix(matrix)
        assert graph == recovered

    def test_matrix_is_symmetric(self):
        """to_matrix should produce symmetric matrix."""
        graph = RamseyGraph(5)
        graph.set_edge(0, 1, True)
        graph.set_edge(2, 3, True)

        matrix = graph.to_matrix()
        assert np.array_equal(matrix, matrix.T)

    def test_copy_is_independent(self):
        """copy should create independent graph."""
        graph = RamseyGraph(5)
        graph.set_edge(0, 1, True)

        copy = graph.copy()
        assert graph == copy

        copy.set_edge(0, 1, False)
        assert graph != copy
        assert graph.get_edge(0, 1) is True

    def test_degree_counting(self):
        """red_degree and blue_degree should sum to n-1."""
        graph = RamseyGraph(6)
        np.random.seed(123)
        for i in range(6):
            for j in range(i + 1, 6):
                graph.set_edge(i, j, bool(np.random.randint(2)))

        for v in range(6):
            assert graph.red_degree(v) + graph.blue_degree(v) == 5

    def test_edge_counting(self):
        """count_red_edges + count_blue_edges should equal total edges."""
        graph = RamseyGraph(7)
        np.random.seed(456)
        for i in range(7):
            for j in range(i + 1, 7):
                graph.set_edge(i, j, bool(np.random.randint(2)))

        total = graph.count_red_edges() + graph.count_blue_edges()
        assert total == num_edges(7)


class TestGraphEquality:
    """Test graph equality comparison."""

    def test_equal_graphs(self):
        """Identical graphs should be equal."""
        g1 = RamseyGraph(5)
        g2 = RamseyGraph(5)
        assert g1 == g2

        g1.set_edge(0, 1, True)
        g2.set_edge(0, 1, True)
        assert g1 == g2

    def test_different_colorings(self):
        """Graphs with different colorings should not be equal."""
        g1 = RamseyGraph(5)
        g2 = RamseyGraph(5)
        g2.set_edge(0, 1, True)
        assert g1 != g2

    def test_different_sizes(self):
        """Graphs with different sizes should not be equal."""
        g1 = RamseyGraph(5)
        g2 = RamseyGraph(6)
        assert g1 != g2


class TestGraphErrors:
    """Test error handling."""

    def test_invalid_size(self):
        """Graph with n < 2 should raise error."""
        with pytest.raises(ValueError):
            RamseyGraph(1)

        with pytest.raises(ValueError):
            RamseyGraph(0)

    def test_self_loop(self):
        """get_edge with i == j should raise error."""
        graph = RamseyGraph(5)
        with pytest.raises(ValueError):
            graph.get_edge(2, 2)

    def test_out_of_range_vertex(self):
        """get_edge with out-of-range vertex should raise error."""
        graph = RamseyGraph(5)
        with pytest.raises(ValueError):
            graph.get_edge(0, 5)

        with pytest.raises(ValueError):
            graph.get_edge(-1, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

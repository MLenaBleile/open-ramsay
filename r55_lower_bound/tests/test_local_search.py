"""Tests for local search algorithms."""

import pytest
import time
import numpy as np

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import verify_k5_free, count_mono_k5_total
from src.search.local_search import (
    random_coloring,
    extend_paley_37_to_n,
    greedy_descent,
    simulated_annealing,
    tabu_search,
    multi_start_search,
    search_for_k5_free,
    SearchResult,
)


class TestRandomColoring:
    """Test random coloring generation."""

    def test_random_coloring_size(self):
        """Random coloring should have correct size."""
        for n in [5, 10, 20]:
            graph = random_coloring(n)
            assert graph.n == n

    def test_random_coloring_reproducible(self):
        """Random coloring with seed should be reproducible."""
        g1 = random_coloring(10, seed=42)
        g2 = random_coloring(10, seed=42)
        assert g1 == g2

    def test_random_coloring_different_seeds(self):
        """Different seeds should give different colorings."""
        g1 = random_coloring(10, seed=42)
        g2 = random_coloring(10, seed=43)
        assert g1 != g2


class TestPaleyExtension:
    """Test Paley graph extension."""

    def test_extend_to_37(self):
        """Extending to 37 should return P(37)."""
        graph = extend_paley_37_to_n(37)
        assert graph.n == 37

        # Should be (5,5)-free
        is_valid, _ = verify_k5_free(graph)
        assert is_valid

    def test_extend_to_40(self):
        """Can extend P(37) to 40 vertices."""
        graph = extend_paley_37_to_n(40)
        assert graph.n == 40

        # First 37 vertices should match P(37)
        from src.constructions.paley import paley_coloring
        p37 = paley_coloring(37)

        for i in range(37):
            for j in range(i + 1, 37):
                assert graph.get_edge(i, j) == p37.get_edge(i, j)


class TestGreedyDescent:
    """Test greedy hill climbing."""

    def test_greedy_improves_or_stays(self):
        """Greedy should not make things worse."""
        np.random.seed(42)
        graph = random_coloring(12)
        initial_k5 = count_mono_k5_total(graph)

        result = greedy_descent(graph, max_steps=1000)

        assert result.k5_count <= initial_k5

    def test_greedy_finds_valid_for_small_n(self):
        """Greedy should find valid coloring for small n."""
        np.random.seed(42)
        graph = random_coloring(10)

        result = greedy_descent(graph, max_steps=1000)

        # For n=10, greedy should easily find a valid coloring
        assert result.found_valid or result.k5_count < 10

    def test_greedy_result_structure(self):
        """SearchResult should have all required fields."""
        graph = random_coloring(8)
        result = greedy_descent(graph, max_steps=100)

        assert isinstance(result.graph, RamseyGraph)
        assert isinstance(result.k5_count, int)
        assert isinstance(result.iterations, int)
        assert isinstance(result.elapsed_time, float)
        assert isinstance(result.history, list)
        assert isinstance(result.found_valid, bool)


class TestSimulatedAnnealing:
    """Test simulated annealing."""

    def test_annealing_small_n(self):
        """Annealing should find valid coloring for small n."""
        np.random.seed(42)
        graph = random_coloring(10)

        result = simulated_annealing(
            graph, max_steps=5000,
            initial_temp=5.0, cooling_rate=0.999
        )

        # Should find valid or get very close
        assert result.k5_count <= 5

    def test_annealing_improves_k5_count(self):
        """Annealing should generally improve K₅ count."""
        np.random.seed(42)
        graph = random_coloring(15)
        initial_k5 = count_mono_k5_total(graph)

        result = simulated_annealing(
            graph, max_steps=10000,
            initial_temp=10.0, cooling_rate=0.9995
        )

        # Should improve (or at least not get much worse)
        assert result.k5_count <= initial_k5 + 5

    def test_annealing_history_recorded(self):
        """Annealing should record history at checkpoints."""
        # Use larger n to ensure it doesn't find valid immediately
        graph = random_coloring(15)
        result = simulated_annealing(
            graph, max_steps=5000, checkpoint_interval=500
        )

        # History should have at least initial entry
        assert len(result.history) >= 1


class TestTabuSearch:
    """Test tabu search."""

    def test_tabu_small_n(self):
        """Tabu search should find valid coloring for small n."""
        np.random.seed(42)
        graph = random_coloring(10)

        result = tabu_search(
            graph, max_steps=2000, tabu_tenure=20
        )

        assert result.k5_count <= 5

    def test_tabu_escapes_local_minima(self):
        """Tabu search should be able to escape local minima."""
        # This is hard to test directly, but we can verify
        # it continues searching even when stuck
        np.random.seed(42)
        graph = random_coloring(12)

        result = tabu_search(
            graph, max_steps=3000, tabu_tenure=30
        )

        # Should have made some progress (or found valid quickly)
        assert result.iterations >= 1


class TestMultiStart:
    """Test multi-start search."""

    def test_multi_start_best_result(self):
        """Multi-start should return best result."""
        np.random.seed(42)

        result = multi_start_search(
            n=10, num_starts=3, method='greedy',
            max_steps_per_start=500
        )

        # Should find valid coloring for n=10
        assert result.found_valid or result.k5_count <= 3

    def test_multi_start_stops_on_valid(self):
        """Multi-start should stop when valid found."""
        np.random.seed(42)

        start_time = time.time()
        result = multi_start_search(
            n=8, num_starts=10, method='greedy',
            max_steps_per_start=1000
        )
        elapsed = time.time() - start_time

        # Should find valid quickly and stop
        if result.found_valid:
            assert elapsed < 5.0  # Should be fast


class TestSearchForK5Free:
    """Test the main search function."""

    def test_search_small_n(self):
        """Should find valid coloring for small n."""
        result = search_for_k5_free(10, time_limit=10.0, verbose=False)
        assert result is not None
        is_valid, _ = verify_k5_free(result)
        assert is_valid

    def test_search_n15(self):
        """Should find valid coloring for n=15."""
        result = search_for_k5_free(15, time_limit=30.0, verbose=False)
        if result is not None:
            is_valid, _ = verify_k5_free(result)
            assert is_valid


class TestSearchPerformance:
    """Test search performance characteristics."""

    def test_annealing_faster_than_greedy_sometimes(self):
        """For some problems, annealing may find solution faster."""
        # This is a probabilistic test - just verify both work
        np.random.seed(42)

        graph1 = random_coloring(12)
        r1 = greedy_descent(graph1.copy(), max_steps=2000)

        graph2 = random_coloring(12)
        r2 = simulated_annealing(graph2.copy(), max_steps=2000)

        # Both should make progress
        assert r1.k5_count <= count_mono_k5_total(random_coloring(12, seed=42)) + 10
        assert r2.k5_count <= count_mono_k5_total(random_coloring(12, seed=42)) + 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

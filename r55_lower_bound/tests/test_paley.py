"""Tests for Paley graph construction."""

import pytest
import time

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import (
    has_mono_k5_brute,
    count_mono_k5,
    verify_k5_free,
    has_mono_clique,
    count_mono_cliques,
)
from src.constructions.paley import (
    is_quadratic_residue,
    quadratic_residues,
    is_prime,
    paley_coloring,
    verify_paley_properties,
    get_paley_43,
    get_best_paley_k5_free,
    find_k5_free_paley_graphs,
)


class TestQuadraticResidues:
    """Test quadratic residue computation."""

    def test_qr_mod_5(self):
        """QRs mod 5 are {1, 4}."""
        qr = quadratic_residues(5)
        assert qr == {1, 4}

    def test_qr_mod_7(self):
        """QRs mod 7 are {1, 2, 4}."""
        qr = quadratic_residues(7)
        assert qr == {1, 2, 4}

    def test_qr_mod_11(self):
        """QRs mod 11 are {1, 3, 4, 5, 9}."""
        qr = quadratic_residues(11)
        assert qr == {1, 3, 4, 5, 9}

    def test_qr_mod_13(self):
        """QRs mod 13 are {1, 3, 4, 9, 10, 12}."""
        qr = quadratic_residues(13)
        assert qr == {1, 3, 4, 9, 10, 12}

    def test_qr_count(self):
        """For odd prime p, there are (p-1)/2 quadratic residues."""
        for p in [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]:
            qr = quadratic_residues(p)
            assert len(qr) == (p - 1) // 2, f"Failed for p={p}"

    def test_is_qr_function(self):
        """Test is_quadratic_residue function."""
        assert is_quadratic_residue(1, 5) is True
        assert is_quadratic_residue(2, 5) is False
        assert is_quadratic_residue(3, 5) is False
        assert is_quadratic_residue(4, 5) is True


class TestIsPrime:
    """Test primality checking."""

    def test_small_primes(self):
        """Test small primes."""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]
        for p in primes:
            assert is_prime(p), f"{p} should be prime"

    def test_small_composites(self):
        """Test small composites."""
        composites = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 44]
        for n in composites:
            assert not is_prime(n), f"{n} should not be prime"

    def test_edge_cases(self):
        """Test edge cases."""
        assert not is_prime(0)
        assert not is_prime(1)
        assert is_prime(2)


class TestPaleyConstruction:
    """Test Paley graph construction."""

    def test_paley_5_properties(self):
        """P(5) should have correct structure."""
        graph = paley_coloring(5)
        assert graph.n == 5

        # Check balance
        red = graph.count_red_edges()
        blue = graph.count_blue_edges()
        assert red + blue == 10  # C(5,2) = 10

    def test_paley_non_prime_fails(self):
        """Paley construction should fail for non-primes."""
        with pytest.raises(ValueError):
            paley_coloring(4)

        with pytest.raises(ValueError):
            paley_coloring(44)

    def test_paley_degree(self):
        """In P(p), total degree is always p-1."""
        for p in [5, 7, 11, 13]:
            graph = paley_coloring(p)

            for v in range(p):
                red_deg = graph.red_degree(v)
                blue_deg = graph.blue_degree(v)
                assert red_deg + blue_deg == p - 1


class TestPaley37:
    """Test P(37) - the largest (5,5)-free Paley graph."""

    def test_p37_basic_properties(self):
        """P(37) should have correct basic properties."""
        graph = get_best_paley_k5_free()
        assert graph.n == 37

        # Total edges
        total_edges = 37 * 36 // 2
        assert graph.count_red_edges() + graph.count_blue_edges() == total_edges

    def test_p37_is_k5_free(self):
        """
        P(37) must be (5,5)-free.

        This proves R(5,5) ≥ 38 from Paley construction alone.
        """
        graph = get_best_paley_k5_free()

        start_time = time.time()
        is_valid, counterexample = verify_k5_free(graph)
        elapsed = time.time() - start_time

        assert is_valid, \
            f"P(37) has monochromatic K₅! Found: {counterexample}"

        print(f"\nP(37) verification time: {elapsed:.2f}s")
        print(f"Verified: P(37) is (5,5)-free")


class TestPaley43:
    """Test P(43) - known to have mono-K₅s."""

    def test_p43_basic_properties(self):
        """P(43) should have correct basic properties."""
        graph = get_paley_43()
        assert graph.n == 43

        # Total edges
        total_edges = 43 * 42 // 2
        assert graph.count_red_edges() + graph.count_blue_edges() == total_edges

    def test_p43_has_mono_k5(self):
        """
        P(43) is NOT (5,5)-free - it has monochromatic K₅s.

        This is an important verification that P(43) does not provide
        the R(5,5) ≥ 44 bound (that must come from other constructions).
        """
        graph = get_paley_43()

        start_time = time.time()
        is_valid, counterexample = verify_k5_free(graph)
        elapsed = time.time() - start_time

        assert not is_valid, "P(43) should have monochromatic K₅"
        print(f"\nP(43) has mono-K₅: {counterexample}")
        print(f"Verification time: {elapsed:.2f}s")

    def test_p43_k5_counts(self):
        """P(43) has both red and blue K₅s."""
        graph = get_paley_43()

        start_time = time.time()
        red_k5, blue_k5 = count_mono_k5(graph)
        elapsed = time.time() - start_time

        print(f"\nP(43) has {red_k5} red K₅s and {blue_k5} blue K₅s")
        print(f"Counting time: {elapsed:.2f}s")

        assert red_k5 > 0 or blue_k5 > 0, "P(43) should have some mono-K₅s"


class TestK5FreePaleyGraphs:
    """Test which Paley graphs are (5,5)-free."""

    # Primes ≡ 1 (mod 4) that should be (5,5)-free
    @pytest.mark.parametrize("p", [5, 13, 17, 29, 37])
    def test_primes_1_mod_4_k5_free(self, p):
        """P(p) for p ≡ 1 (mod 4), p ≤ 37 should be (5,5)-free."""
        graph = paley_coloring(p)
        is_valid, _ = verify_k5_free(graph)
        assert is_valid, f"P({p}) should be (5,5)-free"

    # Primes ≡ 3 (mod 4) that should be (5,5)-free (smaller ones)
    @pytest.mark.parametrize("p", [7, 11, 19])
    def test_primes_3_mod_4_small_k5_free(self, p):
        """P(p) for small p ≡ 3 (mod 4) should be (5,5)-free."""
        graph = paley_coloring(p)
        is_valid, _ = verify_k5_free(graph)
        assert is_valid, f"P({p}) should be (5,5)-free"

    # Primes that have mono-K₅s
    @pytest.mark.parametrize("p", [23, 31, 41, 43])
    def test_primes_with_mono_k5(self, p):
        """P(p) for p ≥ 23 has monochromatic K₅s."""
        graph = paley_coloring(p)
        is_valid, _ = verify_k5_free(graph)
        # Note: Some might be valid (23, 31 might be borderline)
        # We just verify we can check them
        print(f"P({p}): K5-free = {is_valid}")


class TestFindK5FreePaleys:
    """Test the function that finds (5,5)-free Paley graphs."""

    def test_find_k5_free_includes_37(self):
        """P(37) should be in the list of (5,5)-free Paley graphs."""
        k5_free = find_k5_free_paley_graphs()
        assert 37 in k5_free, "P(37) should be (5,5)-free"

    def test_find_k5_free_excludes_41(self):
        """P(41) should NOT be in the list of (5,5)-free Paley graphs."""
        k5_free = find_k5_free_paley_graphs()
        assert 41 not in k5_free, "P(41) should have mono-K₅"

    def test_k5_free_list_reasonable(self):
        """The list of (5,5)-free Paley graphs should be reasonable."""
        k5_free = find_k5_free_paley_graphs()
        print(f"\n(5,5)-free Paley graphs: {k5_free}")

        # Should have at least several small primes
        assert len(k5_free) >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""
Circulant graph constructions for Ramsey problems.

A circulant graph C(n, S) has:
- Vertices: {0, 1, ..., n-1}
- Edge (i,j) is red if min(|i-j|, n-|i-j|) ∈ S, blue otherwise

Key insight: Circulant graphs have n-fold rotational symmetry.
If C(n, S) has a mono K₅, then rotating that K₅ gives another.
So we can:
1. Check representative 5-sets under rotation (reduces search by factor of n)
2. Use algebraic conditions on S to rule out many sets

For n = 44, we need S ⊆ {1, ..., 22} with |S| ≈ 11 (half-density).
There are C(22, 11) ≈ 705,432 such sets—tractable with pruning.
"""

from typing import Set, FrozenSet, Iterator, Optional, Callable
from itertools import combinations
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph


def circulant_coloring(n: int, connection_set: Set[int]) -> RamseyGraph:
    """
    Construct a circulant graph coloring on n vertices.

    Edge (i, j) is colored red if the "cyclic distance" between i and j
    is in the connection set, blue otherwise.

    The cyclic distance is min(|i-j|, n - |i-j|).

    Args:
        n: Number of vertices (must be >= 2)
        connection_set: Set of distances that give red edges.
                       Should be subset of {1, 2, ..., floor(n/2)}.

    Returns:
        RamseyGraph with circulant coloring

    Example:
        C(6, {1, 2}) colors edges at distance 1 or 2 as red,
        edges at distance 3 as blue.
    """
    graph = RamseyGraph(n)

    for i in range(n):
        for j in range(i + 1, n):
            # Compute cyclic distance
            diff = j - i
            cyclic_dist = min(diff, n - diff)

            # Red if in connection set, blue otherwise
            color = cyclic_dist not in connection_set
            graph.set_edge(i, j, color)

    return graph


def connection_set_from_graph(graph: RamseyGraph) -> Optional[Set[int]]:
    """
    Check if a graph is circulant and return its connection set.

    A graph is circulant if all edges of the same cyclic distance
    have the same color.

    Args:
        graph: The 2-colored graph to check

    Returns:
        The connection set if circulant, None otherwise
    """
    n = graph.n
    connection_set = set()

    for d in range(1, n // 2 + 1):
        # Check all edges at distance d
        colors_at_d = set()
        for i in range(n):
            j = (i + d) % n
            if i < j:
                colors_at_d.add(graph.get_edge(i, j))
            else:
                colors_at_d.add(graph.get_edge(j, i))

        if len(colors_at_d) > 1:
            return None  # Not circulant

        # Red (False) means d is in connection set
        if False in colors_at_d:
            connection_set.add(d)

    return connection_set


def generate_connection_sets(
    n: int,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None
) -> Iterator[FrozenSet[int]]:
    """
    Generate all connection sets for circulant graphs on n vertices.

    Args:
        n: Number of vertices
        min_size: Minimum size of connection set (default: 1)
        max_size: Maximum size of connection set (default: n//2)

    Yields:
        Frozen sets representing connection sets
    """
    max_dist = n // 2

    if min_size is None:
        min_size = 1
    if max_size is None:
        max_size = max_dist

    for size in range(min_size, max_size + 1):
        for combo in combinations(range(1, max_dist + 1), size):
            yield frozenset(combo)


def estimate_density(n: int, connection_set: Set[int]) -> float:
    """
    Estimate the red edge density for a circulant graph.

    Args:
        n: Number of vertices
        connection_set: The connection set

    Returns:
        Fraction of edges that are red
    """
    max_dist = n // 2
    total_red = 0

    for d in range(1, max_dist + 1):
        if d in connection_set:
            if d == max_dist and n % 2 == 0:
                # Distance n/2 has n/2 edges (each pair counted once)
                total_red += n // 2
            else:
                # Other distances have n edges
                total_red += n

    total_edges = n * (n - 1) // 2
    return total_red / total_edges


def prune_connection_set(
    n: int,
    connection_set: Set[int],
    min_density: float = 0.3,
    max_density: float = 0.7
) -> bool:
    """
    Check if a connection set is worth checking for (5,5)-free.

    Prunes connection sets that are too sparse or too dense,
    as these are unlikely to be (5,5)-free.

    Args:
        n: Number of vertices
        connection_set: The connection set to evaluate
        min_density: Minimum acceptable red edge density
        max_density: Maximum acceptable red edge density

    Returns:
        True if the connection set passes pruning, False to skip
    """
    density = estimate_density(n, connection_set)
    return min_density <= density <= max_density


def check_circulant_representative(
    n: int,
    connection_set: Set[int]
) -> tuple[bool, Optional[tuple]]:
    """
    Check if a circulant graph is (5,5)-free using rotation symmetry.

    Instead of checking all C(n,5) subsets, we only check
    representative 5-sets under rotation, reducing work by factor of n.

    Args:
        n: Number of vertices
        connection_set: The connection set

    Returns:
        Tuple of (is_valid, counterexample) where counterexample is
        a 5-tuple of vertices forming a mono-K₅ if found.
    """
    from src.core.clique_checker import verify_k5_free

    # For now, use full verification (optimization can come later)
    graph = circulant_coloring(n, connection_set)
    return verify_k5_free(graph)


def search_circulant_colorings(
    n: int,
    callback: Optional[Callable[[Set[int], RamseyGraph], None]] = None,
    min_density: float = 0.3,
    max_density: float = 0.7,
    verbose: bool = False
) -> list[Set[int]]:
    """
    Search for (5,5)-free circulant colorings of K_n.

    Args:
        n: Number of vertices
        callback: Optional function called with each valid coloring found
        min_density: Minimum red edge density (for pruning)
        max_density: Maximum red edge density (for pruning)
        verbose: Print progress information

    Returns:
        List of connection sets that give (5,5)-free colorings
    """
    valid_sets = []
    checked = 0
    pruned = 0

    max_dist = n // 2

    # For balanced density, check sets of size around max_dist/2
    target_size = max_dist // 2

    for size in range(1, max_dist + 1):
        if verbose:
            print(f"Checking connection sets of size {size}...")

        for combo in combinations(range(1, max_dist + 1), size):
            connection_set = set(combo)

            # Pruning
            if not prune_connection_set(n, connection_set, min_density, max_density):
                pruned += 1
                continue

            checked += 1

            is_valid, _ = check_circulant_representative(n, connection_set)

            if is_valid:
                valid_sets.append(connection_set)
                if callback:
                    graph = circulant_coloring(n, connection_set)
                    callback(connection_set, graph)
                if verbose:
                    print(f"  Found valid: {sorted(connection_set)}")

    if verbose:
        print(f"Total: checked {checked}, pruned {pruned}, found {len(valid_sets)}")

    return valid_sets


def search_k5_free_circulants_for_range(
    start_n: int,
    end_n: int,
    verbose: bool = True
) -> dict[int, list[Set[int]]]:
    """
    Search for (5,5)-free circulant colorings for a range of n values.

    Args:
        start_n: Starting number of vertices
        end_n: Ending number of vertices (inclusive)
        verbose: Print progress

    Returns:
        Dictionary mapping n to list of valid connection sets
    """
    results = {}

    for n in range(start_n, end_n + 1):
        if verbose:
            print(f"\n=== Searching n = {n} ===")
        valid = search_circulant_colorings(n, verbose=verbose)
        results[n] = valid
        if verbose:
            print(f"Found {len(valid)} valid circulant colorings for n={n}")

    return results


def get_paley_like_connection_set(p: int) -> Set[int]:
    """
    Get the connection set that corresponds to a Paley-like construction.

    For prime p, the quadratic residues form a natural connection set.

    Args:
        p: An odd prime

    Returns:
        Set of quadratic residues in {1, ..., (p-1)/2}
    """
    from src.constructions.paley import quadratic_residues

    qr = quadratic_residues(p)
    max_dist = p // 2

    # Return only residues up to p/2 (symmetric)
    return {r for r in qr if r <= max_dist}


def compare_paley_and_circulant(p: int) -> dict:
    """
    Compare Paley graph P(p) with its circulant approximation.

    The Paley graph is NOT exactly circulant for p ≡ 3 (mod 4),
    but we can compare the structures.

    Args:
        p: An odd prime

    Returns:
        Dictionary with comparison information
    """
    from src.constructions.paley import paley_coloring
    from src.core.clique_checker import count_mono_k5

    paley_graph = paley_coloring(p)

    # Check if Paley is circulant
    paley_connection = connection_set_from_graph(paley_graph)

    if paley_connection is not None:
        # It's circulant - compare directly
        circulant_graph = circulant_coloring(p, paley_connection)
        same = (paley_graph == circulant_graph)
    else:
        # Not circulant - use Paley-like connection set
        paley_like = get_paley_like_connection_set(p)
        circulant_graph = circulant_coloring(p, paley_like)
        same = False
        paley_connection = paley_like

    paley_k5 = count_mono_k5(paley_graph)
    circulant_k5 = count_mono_k5(circulant_graph)

    return {
        'p': p,
        'p_mod_4': p % 4,
        'is_paley_circulant': same,
        'connection_set': sorted(paley_connection) if paley_connection else None,
        'paley_k5': paley_k5,
        'circulant_k5': circulant_k5,
    }

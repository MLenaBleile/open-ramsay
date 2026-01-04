"""
Algorithms for detecting monochromatic K₅ in a 2-colored complete graph.

We implement multiple algorithms because:
1. Brute force: O(n^5) but simple, good for verification
2. Early termination: Stop as soon as K₅ found
3. Batch checking: Numpy vectorization for speed
4. Incremental: Check only affected 5-sets when one edge changes

The incremental checker is crucial for local search.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import numpy as np
from itertools import combinations

if TYPE_CHECKING:
    from .graph import RamseyGraph


def _is_mono_clique(graph: RamseyGraph, vertices: tuple, color: bool) -> bool:
    """
    Check if the given vertices form a monochromatic clique of the given color.

    Args:
        graph: The colored graph
        vertices: Tuple of vertex indices
        color: The color to check for (False=red, True=blue)

    Returns:
        True if all edges between vertices have the given color
    """
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            if graph.get_edge(vertices[i], vertices[j]) != color:
                return False
    return True


def has_mono_k5_brute(graph: RamseyGraph) -> bool:
    """
    Check if the graph contains any monochromatic K₅.

    Uses brute force enumeration of all C(n,5) 5-subsets.
    Early terminates on first K₅ found.

    Args:
        graph: The 2-colored complete graph

    Returns:
        True if a monochromatic K₅ exists (either red or blue)
    """
    if graph.n < 5:
        return False

    for subset in combinations(range(graph.n), 5):
        if _is_mono_clique(graph, subset, False):  # Red K₅
            return True
        if _is_mono_clique(graph, subset, True):  # Blue K₅
            return True

    return False


def find_mono_k5_brute(graph: RamseyGraph) -> Optional[tuple[tuple, bool]]:
    """
    Find a monochromatic K₅ if one exists.

    Args:
        graph: The 2-colored complete graph

    Returns:
        Tuple of (vertices, color) if K₅ found, None otherwise.
        Color is False for red, True for blue.
    """
    if graph.n < 5:
        return None

    for subset in combinations(range(graph.n), 5):
        if _is_mono_clique(graph, subset, False):
            return (subset, False)
        if _is_mono_clique(graph, subset, True):
            return (subset, True)

    return None


def count_mono_k5(graph: RamseyGraph) -> tuple[int, int]:
    """
    Count all monochromatic K₅ subgraphs.

    Args:
        graph: The 2-colored complete graph

    Returns:
        Tuple of (red_k5_count, blue_k5_count)
    """
    if graph.n < 5:
        return (0, 0)

    red_count = 0
    blue_count = 0

    for subset in combinations(range(graph.n), 5):
        if _is_mono_clique(graph, subset, False):
            red_count += 1
        elif _is_mono_clique(graph, subset, True):
            blue_count += 1

    return (red_count, blue_count)


def count_mono_k5_total(graph: RamseyGraph) -> int:
    """
    Count total monochromatic K₅ subgraphs (red + blue).

    Args:
        graph: The 2-colored complete graph

    Returns:
        Total count of monochromatic K₅ subgraphs
    """
    red, blue = count_mono_k5(graph)
    return red + blue


def find_all_mono_k5(graph: RamseyGraph) -> tuple[list[tuple], list[tuple]]:
    """
    Find all monochromatic K₅ subgraphs.

    Args:
        graph: The 2-colored complete graph

    Returns:
        Tuple of (red_k5_list, blue_k5_list) where each list contains
        tuples of 5 vertex indices.
    """
    if graph.n < 5:
        return ([], [])

    red_cliques = []
    blue_cliques = []

    for subset in combinations(range(graph.n), 5):
        if _is_mono_clique(graph, subset, False):
            red_cliques.append(subset)
        elif _is_mono_clique(graph, subset, True):
            blue_cliques.append(subset)

    return (red_cliques, blue_cliques)


def check_edge_flip_delta(
    graph: RamseyGraph,
    edge: tuple[int, int],
    current_count: Optional[int] = None
) -> int:
    """
    Compute the change in monochromatic K₅ count if an edge is flipped.

    This is the key operation for local search. Instead of recounting
    all K₅ subgraphs, we only check the C(n-2, 3) subsets containing
    the flipped edge.

    Args:
        graph: The 2-colored complete graph
        edge: The edge (i, j) to consider flipping
        current_count: Current total K₅ count (optional, for verification)

    Returns:
        Change in K₅ count: new_count - old_count (negative means improvement)
    """
    i, j = edge
    if i > j:
        i, j = j, i

    n = graph.n
    if n < 5:
        return 0

    current_color = graph.get_edge(i, j)
    new_color = not current_color

    # Get all other vertices
    other_vertices = [v for v in range(n) if v != i and v != j]

    destroyed = 0  # K₅s that currently exist but won't after flip
    created = 0    # K₅s that don't exist but will after flip

    # Check all 5-subsets containing both i and j
    # We need 3 more vertices from the remaining n-2
    for triple in combinations(other_vertices, 3):
        subset = (i, j) + triple

        # Check if this is currently a monochromatic K₅
        # We only need to check the color matching the edge (i,j)
        # because flipping (i,j) can only affect K₅s of that color

        # Count edges of each color in the subset (excluding edge (i,j))
        edges_in_subset = []
        for a in range(5):
            for b in range(a + 1, 5):
                if not (subset[a] in (i, j) and subset[b] in (i, j)):
                    edges_in_subset.append((subset[a], subset[b]))

        # Check edges excluding (i,j)
        all_match_current = all(
            graph.get_edge(a, b) == current_color
            for a, b in edges_in_subset
        )
        all_match_new = all(
            graph.get_edge(a, b) == new_color
            for a, b in edges_in_subset
        )

        if all_match_current:
            # This is currently a mono-K₅ of current_color, will be destroyed
            destroyed += 1

        if all_match_new:
            # This will become a mono-K₅ of new_color after flip
            created += 1

    return created - destroyed


def check_edge_flip_delta_fast(
    graph: RamseyGraph,
    edge: tuple[int, int],
    adjacency_matrix: Optional[np.ndarray] = None
) -> int:
    """
    Faster version using numpy operations.

    Args:
        graph: The 2-colored complete graph
        edge: The edge (i, j) to consider flipping
        adjacency_matrix: Precomputed adjacency matrix (optional)

    Returns:
        Change in K₅ count: new_count - old_count
    """
    i, j = edge
    if i > j:
        i, j = j, i

    n = graph.n
    if n < 5:
        return 0

    if adjacency_matrix is None:
        adj = graph.to_matrix()
    else:
        adj = adjacency_matrix

    current_color = adj[i, j]
    new_color = not current_color

    # Get all other vertices
    others = [v for v in range(n) if v != i and v != j]

    destroyed = 0
    created = 0

    # For each triple of other vertices
    for idx, (a, b, c) in enumerate(combinations(others, 3)):
        # The subset is {i, j, a, b, c}
        # Edges NOT involving (i,j): (i,a), (i,b), (i,c), (j,a), (j,b), (j,c), (a,b), (a,c), (b,c)
        other_edges = [
            adj[i, a], adj[i, b], adj[i, c],
            adj[j, a], adj[j, b], adj[j, c],
            adj[a, b], adj[a, c], adj[b, c]
        ]

        # Check if all other edges match current color -> destroyed
        if all(e == current_color for e in other_edges):
            destroyed += 1

        # Check if all other edges match new color -> created
        if all(e == new_color for e in other_edges):
            created += 1

    return created - destroyed


def verify_k5_free(graph: RamseyGraph) -> tuple[bool, Optional[tuple]]:
    """
    Verify that a graph is K₅-free in both colors.

    Args:
        graph: The 2-colored complete graph

    Returns:
        Tuple of (is_valid, counterexample) where counterexample is
        (vertices, color) if a K₅ was found, None if valid.
    """
    result = find_mono_k5_brute(graph)
    if result is None:
        return (True, None)
    else:
        return (False, result)


def has_mono_clique(graph: RamseyGraph, k: int, color: bool) -> bool:
    """
    Check if the graph contains a monochromatic K_k of the given color.

    Args:
        graph: The 2-colored complete graph
        k: Clique size to search for
        color: Color to search for (False=red, True=blue)

    Returns:
        True if such a clique exists
    """
    if graph.n < k:
        return False

    for subset in combinations(range(graph.n), k):
        if _is_mono_clique(graph, subset, color):
            return True
    return False


def count_mono_cliques(graph: RamseyGraph, k: int) -> tuple[int, int]:
    """
    Count monochromatic K_k subgraphs of each color.

    Args:
        graph: The 2-colored complete graph
        k: Clique size to count

    Returns:
        Tuple of (red_count, blue_count)
    """
    if graph.n < k:
        return (0, 0)

    red_count = 0
    blue_count = 0

    for subset in combinations(range(graph.n), k):
        if _is_mono_clique(graph, subset, False):
            red_count += 1
        elif _is_mono_clique(graph, subset, True):
            blue_count += 1

    return (red_count, blue_count)

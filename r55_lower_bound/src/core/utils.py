"""Utility functions for Ramsey graph computations."""

from typing import Iterator
import numpy as np


def combinations_indices(n: int, k: int) -> Iterator[tuple]:
    """
    Generate all k-combinations of indices 0..n-1.

    This is a generator that yields tuples of indices, more memory-efficient
    than itertools.combinations for large n.

    Args:
        n: Number of elements to choose from (0 to n-1)
        k: Size of each combination

    Yields:
        Tuples of k distinct indices in increasing order
    """
    if k > n or k < 0:
        return
    if k == 0:
        yield ()
        return

    # Use itertools for simplicity and speed
    from itertools import combinations
    for combo in combinations(range(n), k):
        yield combo


def edge_index(i: int, j: int, n: int) -> int:
    """
    Convert vertex pair (i, j) to linear index in upper triangular storage.

    For a graph with n vertices, edges are stored in a flat array where
    edge (i, j) with i < j is at position: i * n - i * (i + 1) // 2 + j - i - 1

    Args:
        i: First vertex (must be < j)
        j: Second vertex
        n: Total number of vertices

    Returns:
        Linear index into the edge array
    """
    if i > j:
        i, j = j, i
    return i * n - i * (i + 1) // 2 + j - i - 1


def vertex_pair(idx: int, n: int) -> tuple[int, int]:
    """
    Convert linear index back to vertex pair (i, j).

    Inverse of edge_index.

    Args:
        idx: Linear index in edge array
        n: Total number of vertices

    Returns:
        Tuple (i, j) with i < j
    """
    # Binary search for i
    i = 0
    remaining = idx
    while True:
        edges_from_i = n - i - 1
        if remaining < edges_from_i:
            j = i + 1 + remaining
            return (i, j)
        remaining -= edges_from_i
        i += 1


def num_edges(n: int) -> int:
    """Return the number of edges in K_n."""
    return n * (n - 1) // 2


def binomial(n: int, k: int) -> int:
    """Compute binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result

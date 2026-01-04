"""
Local search for Ramsey colorings.

Key insight: We don't need to find a GLOBAL optimum.
We need to find ANY coloring with K₅ count = 0.

This is a constraint satisfaction problem, not optimization.
But treating it as optimization (minimize violations) often works.

Methods implemented:
1. Simulated Annealing: Random walk with decreasing temperature
2. Tabu Search: Track forbidden moves to escape local minima
3. Greedy Hill Climbing: Always take best improving move
"""

from typing import Optional, Callable, Tuple, List
import numpy as np
import time
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import (
    count_mono_k5_total,
    check_edge_flip_delta,
)


class SearchResult:
    """Result of a local search run."""

    def __init__(
        self,
        graph: RamseyGraph,
        k5_count: int,
        iterations: int,
        elapsed_time: float,
        history: List[int],
        found_valid: bool
    ):
        self.graph = graph
        self.k5_count = k5_count
        self.iterations = iterations
        self.elapsed_time = elapsed_time
        self.history = history  # K₅ count at each checkpoint
        self.found_valid = found_valid

    def __repr__(self):
        status = "VALID" if self.found_valid else f"k5={self.k5_count}"
        return f"SearchResult({status}, iters={self.iterations}, time={self.elapsed_time:.2f}s)"


def random_coloring(n: int, seed: Optional[int] = None) -> RamseyGraph:
    """Generate a random 2-coloring of K_n."""
    if seed is not None:
        np.random.seed(seed)

    graph = RamseyGraph(n)
    num_edges = n * (n - 1) // 2

    for idx in range(num_edges):
        graph.edges[idx] = np.random.random() < 0.5

    return graph


def extend_paley_37_to_n(n: int) -> RamseyGraph:
    """
    Extend the Paley graph P(37) to n vertices.

    Uses random coloring for edges involving new vertices.

    Args:
        n: Target number of vertices (n >= 37)

    Returns:
        RamseyGraph with n vertices
    """
    from src.constructions.paley import paley_coloring

    if n < 37:
        raise ValueError(f"n must be >= 37, got {n}")

    base = paley_coloring(37)

    if n == 37:
        return base

    graph = RamseyGraph(n)

    # Copy P(37)
    for i in range(37):
        for j in range(i + 1, 37):
            graph.set_edge(i, j, base.get_edge(i, j))

    # Random coloring for new edges
    for v in range(37, n):
        for u in range(v):
            graph.set_edge(u, v, np.random.random() < 0.5)

    return graph


def greedy_descent(
    graph: RamseyGraph,
    max_steps: int = 10000,
    verbose: bool = False
) -> SearchResult:
    """
    Greedy hill climbing - always flip the best edge.

    Args:
        graph: Initial coloring (will be modified in place)
        max_steps: Maximum iterations
        verbose: Print progress

    Returns:
        SearchResult with final state
    """
    start_time = time.time()
    history = []

    current_k5 = count_mono_k5_total(graph)
    history.append(current_k5)

    n = graph.n
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    for step in range(max_steps):
        if current_k5 == 0:
            break

        # Find best edge to flip
        best_delta = 0
        best_edge = None

        for edge in edges:
            delta = check_edge_flip_delta(graph, edge)
            if delta < best_delta:
                best_delta = delta
                best_edge = edge

        if best_edge is None or best_delta >= 0:
            # No improving move - stuck in local minimum
            if verbose:
                print(f"Stuck at step {step}, k5={current_k5}")
            break

        # Apply the move
        graph.flip_edge(*best_edge)
        current_k5 += best_delta

        if step % 100 == 0:
            history.append(current_k5)
            if verbose:
                print(f"Step {step}: k5={current_k5}")

    elapsed = time.time() - start_time
    return SearchResult(
        graph=graph,
        k5_count=current_k5,
        iterations=step + 1,
        elapsed_time=elapsed,
        history=history,
        found_valid=(current_k5 == 0)
    )


def simulated_annealing(
    graph: RamseyGraph,
    max_steps: int = 100000,
    initial_temp: float = 10.0,
    cooling_rate: float = 0.9995,
    min_temp: float = 0.01,
    verbose: bool = False,
    checkpoint_interval: int = 1000
) -> SearchResult:
    """
    Simulated annealing for Ramsey coloring.

    Args:
        graph: Initial coloring (will be modified in place)
        max_steps: Maximum iterations
        initial_temp: Starting temperature
        cooling_rate: Multiply temp by this each step
        min_temp: Stop when temp falls below this
        verbose: Print progress
        checkpoint_interval: How often to record history

    Returns:
        SearchResult with final state
    """
    start_time = time.time()
    history = []

    current_k5 = count_mono_k5_total(graph)
    best_k5 = current_k5
    best_graph = graph.copy()

    history.append(current_k5)

    n = graph.n
    num_edges = n * (n - 1) // 2

    temp = initial_temp
    accepted = 0

    for step in range(max_steps):
        if current_k5 == 0:
            break

        if temp < min_temp:
            if verbose:
                print(f"Temperature too low at step {step}")
            break

        # Pick random edge
        idx = np.random.randint(num_edges)
        i, j = 0, 0
        remaining = idx
        for ii in range(n):
            edges_from_ii = n - ii - 1
            if remaining < edges_from_ii:
                i = ii
                j = ii + 1 + remaining
                break
            remaining -= edges_from_ii

        edge = (i, j)
        delta = check_edge_flip_delta(graph, edge)

        # Accept or reject
        if delta <= 0:
            # Improving or neutral - always accept
            accept = True
        else:
            # Worsening - accept with probability exp(-delta/temp)
            prob = np.exp(-delta / temp)
            accept = np.random.random() < prob

        if accept:
            graph.flip_edge(i, j)
            current_k5 += delta
            accepted += 1

            if current_k5 < best_k5:
                best_k5 = current_k5
                best_graph = graph.copy()

        # Cool down
        temp *= cooling_rate

        # Checkpoint
        if step % checkpoint_interval == 0:
            history.append(current_k5)
            if verbose:
                print(f"Step {step}: k5={current_k5}, best={best_k5}, temp={temp:.4f}")

    elapsed = time.time() - start_time

    # Return best found, not necessarily final
    return SearchResult(
        graph=best_graph,
        k5_count=best_k5,
        iterations=step + 1,
        elapsed_time=elapsed,
        history=history,
        found_valid=(best_k5 == 0)
    )


def tabu_search(
    graph: RamseyGraph,
    max_steps: int = 50000,
    tabu_tenure: int = 50,
    verbose: bool = False,
    checkpoint_interval: int = 500
) -> SearchResult:
    """
    Tabu search for Ramsey coloring.

    Args:
        graph: Initial coloring (will be modified in place)
        max_steps: Maximum iterations
        tabu_tenure: How long edges stay forbidden
        verbose: Print progress
        checkpoint_interval: How often to record history

    Returns:
        SearchResult with final state
    """
    start_time = time.time()
    history = []

    current_k5 = count_mono_k5_total(graph)
    best_k5 = current_k5
    best_graph = graph.copy()

    history.append(current_k5)

    n = graph.n
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

    # Tabu list: edge -> step when it becomes non-tabu
    tabu = {}

    for step in range(max_steps):
        if current_k5 == 0:
            break

        # Find best non-tabu move (or best tabu if it improves on best_k5)
        best_delta = float('inf')
        best_edge = None

        for edge in edges:
            delta = check_edge_flip_delta(graph, edge)
            is_tabu = tabu.get(edge, 0) > step

            # Aspiration: allow tabu move if it beats best
            if is_tabu and current_k5 + delta >= best_k5:
                continue

            if delta < best_delta:
                best_delta = delta
                best_edge = edge

        if best_edge is None:
            if verbose:
                print(f"No valid move at step {step}")
            break

        # Apply move
        graph.flip_edge(*best_edge)
        current_k5 += best_delta

        # Add to tabu list
        tabu[best_edge] = step + tabu_tenure

        # Update best
        if current_k5 < best_k5:
            best_k5 = current_k5
            best_graph = graph.copy()

        # Checkpoint
        if step % checkpoint_interval == 0:
            history.append(current_k5)
            if verbose:
                print(f"Step {step}: k5={current_k5}, best={best_k5}")

    elapsed = time.time() - start_time

    return SearchResult(
        graph=best_graph,
        k5_count=best_k5,
        iterations=step + 1,
        elapsed_time=elapsed,
        history=history,
        found_valid=(best_k5 == 0)
    )


def multi_start_search(
    n: int,
    num_starts: int = 10,
    method: str = 'annealing',
    max_steps_per_start: int = 50000,
    verbose: bool = False,
    initial_graph_fn: Optional[Callable[[int], RamseyGraph]] = None
) -> SearchResult:
    """
    Run multiple independent searches with different starting points.

    Args:
        n: Number of vertices
        num_starts: Number of independent searches
        method: 'annealing', 'tabu', or 'greedy'
        max_steps_per_start: Max steps for each search
        verbose: Print progress
        initial_graph_fn: Function to generate initial graphs (default: random)

    Returns:
        Best SearchResult across all starts
    """
    if initial_graph_fn is None:
        initial_graph_fn = lambda n: random_coloring(n)

    best_result = None

    for start in range(num_starts):
        if verbose:
            print(f"\n=== Start {start + 1}/{num_starts} ===")

        graph = initial_graph_fn(n)

        if method == 'annealing':
            result = simulated_annealing(
                graph, max_steps=max_steps_per_start, verbose=verbose
            )
        elif method == 'tabu':
            result = tabu_search(
                graph, max_steps=max_steps_per_start, verbose=verbose
            )
        elif method == 'greedy':
            result = greedy_descent(
                graph, max_steps=max_steps_per_start, verbose=verbose
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        if best_result is None or result.k5_count < best_result.k5_count:
            best_result = result

        if result.found_valid:
            if verbose:
                print(f"Found valid coloring!")
            break

        if verbose:
            print(f"Best so far: k5={best_result.k5_count}")

    return best_result


def search_for_k5_free(
    n: int,
    time_limit: float = 60.0,
    verbose: bool = True
) -> Optional[RamseyGraph]:
    """
    Search for a (5,5)-free coloring of K_n.

    Uses multiple methods with time budgeting.

    Args:
        n: Number of vertices
        time_limit: Maximum time in seconds
        verbose: Print progress

    Returns:
        Valid RamseyGraph if found, None otherwise
    """
    start_time = time.time()

    # Try greedy from Paley extension first (if n >= 37)
    if n >= 37:
        if verbose:
            print("Trying greedy from Paley extension...")
        for _ in range(5):
            graph = extend_paley_37_to_n(n)
            result = greedy_descent(graph, max_steps=10000)
            if result.found_valid:
                return result.graph
            if time.time() - start_time > time_limit:
                return None

    # Try simulated annealing with multiple starts
    remaining = time_limit - (time.time() - start_time)
    if remaining > 10:
        if verbose:
            print("Trying simulated annealing...")
        steps_per_start = int(remaining * 1000)
        result = multi_start_search(
            n, num_starts=5, method='annealing',
            max_steps_per_start=steps_per_start,
            verbose=verbose
        )
        if result.found_valid:
            return result.graph

    # Try tabu search
    remaining = time_limit - (time.time() - start_time)
    if remaining > 5:
        if verbose:
            print("Trying tabu search...")
        steps_per_start = int(remaining * 500)
        result = multi_start_search(
            n, num_starts=3, method='tabu',
            max_steps_per_start=steps_per_start,
            verbose=verbose
        )
        if result.found_valid:
            return result.graph

    return None

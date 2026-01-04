#!/usr/bin/env python3
"""
Find a (5,5)-free 2-coloring of K_42 to verify R(5,5) >= 43.

Uses multiple search strategies:
1. Start from random graphs
2. Start from Cyclic(42) base with modifications
3. Use tabu search for escaping local minima
"""

import sys
import time
import random
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free
from src.search.local_search import simulated_annealing, tabu_search, random_coloring
from src.constructions.exoo42 import cyclic42_base


def search_from_random(seed: int, max_steps: int = 200000) -> tuple:
    """Search starting from a random coloring."""
    np.random.seed(seed)
    random.seed(seed)

    graph = random_coloring(42, seed=seed)

    result = simulated_annealing(
        graph,
        max_steps=max_steps,
        initial_temp=10.0,
        cooling_rate=0.99998,
        verbose=False
    )

    return seed, result.k5_count, result.found_valid, result.graph if result.found_valid else None


def search_from_cyclic(seed: int, max_steps: int = 200000) -> tuple:
    """Search starting from Cyclic(42) base with random perturbations."""
    np.random.seed(seed)
    random.seed(seed)

    graph = cyclic42_base()

    # Apply random perturbations (flip ~5% of edges)
    num_edges = 42 * 41 // 2
    num_flips = num_edges // 20
    for _ in range(num_flips):
        i = random.randint(0, 41)
        j = random.randint(0, 41)
        if i != j:
            if i > j:
                i, j = j, i
            current = graph.get_edge(i, j)
            graph.set_edge(i, j, not current)

    result = simulated_annealing(
        graph,
        max_steps=max_steps,
        initial_temp=10.0,
        cooling_rate=0.99998,
        verbose=False
    )

    return seed, result.k5_count, result.found_valid, result.graph if result.found_valid else None


def search_with_tabu(seed: int, max_steps: int = 100000) -> tuple:
    """Search using tabu search for better local minima escape."""
    np.random.seed(seed)
    random.seed(seed)

    graph = random_coloring(42, seed=seed)

    result = tabu_search(
        graph,
        max_steps=max_steps,
        tabu_tenure=50,
        verbose=False
    )

    return seed, result.k5_count, result.found_valid, result.graph if result.found_valid else None


def verify_and_save(graph: RamseyGraph, filename: str):
    """Verify a graph is (5,5)-free and save it."""
    is_valid, counter = verify_k5_free(graph)
    if is_valid:
        red_k5, blue_k5 = count_mono_k5(graph)
        print(f"\n*** SUCCESS! Found (5,5)-free K_42! ***")
        print(f"Verification: {red_k5} red K5s, {blue_k5} blue K5s")

        # Save the graph edges
        with open(filename, 'w') as f:
            f.write("# (5,5)-free 2-coloring of K_42\n")
            f.write("# Proves R(5,5) >= 43\n")
            f.write("# Edge format: i j color (0=red, 1=blue)\n")
            for i in range(42):
                for j in range(i + 1, 42):
                    color = 1 if graph.get_edge(i, j) else 0
                    f.write(f"{i} {j} {color}\n")
        print(f"Graph saved to {filename}")
        return True
    return False


def main():
    print("=" * 60)
    print("Searching for (5,5)-free K_42 to verify R(5,5) >= 43")
    print("=" * 60)

    # Quick initial tests
    print("\n--- Quick tests with different starting points ---")

    best_score = float('inf')
    best_graph = None

    # Try a few quick runs
    for i in range(5):
        seed = 42 + i
        print(f"\nRun {i+1}/5 from random (seed={seed})...")

        np.random.seed(seed)
        graph = random_coloring(42, seed=seed)

        result = simulated_annealing(
            graph,
            max_steps=50000,
            initial_temp=8.0,
            cooling_rate=0.9999,
            checkpoint_interval=10000,
            verbose=True
        )

        if result.found_valid:
            print(f"\n*** FOUND VALID COLORING! ***")
            verify_and_save(result.graph, "r55_42_found.txt")
            return

        if result.k5_count < best_score:
            best_score = result.k5_count
            best_graph = result.graph.copy()
            print(f"  New best: {best_score} violations")

    # Continue from best found so far
    if best_graph is not None:
        print(f"\n--- Continuing from best found ({best_score} violations) ---")

        result = simulated_annealing(
            best_graph,
            max_steps=200000,
            initial_temp=5.0,
            cooling_rate=0.99998,
            checkpoint_interval=20000,
            verbose=True
        )

        if result.found_valid:
            print(f"\n*** FOUND VALID COLORING! ***")
            verify_and_save(result.graph, "r55_42_found.txt")
            return

        print(f"\nBest found: {result.k5_count} violations")

    print("\n--- Search complete ---")
    print(f"Best score achieved: {best_score if best_graph else 'N/A'}")
    print("Did not find a (5,5)-free coloring in this run.")
    print("The known R(5,5) >= 43 bound requires more extensive search or")
    print("obtaining the graph data from McKay's ANU repository.")


if __name__ == "__main__":
    main()

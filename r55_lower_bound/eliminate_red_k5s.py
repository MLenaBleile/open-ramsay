#!/usr/bin/env python3
"""
Start with Cyclic(42) that has 0 blue K5s but many red K5s.
Use local search to flip edges and eliminate red K5s without creating blue K5s.
"""

import sys
import random
import math
from itertools import combinations

sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5


def construct_cyclic42_no_blue_k5():
    """
    Construct Cyclic(42) with the distance coloring that has 0 blue K5s.
    Red distances: {1, 2, 3, 4, 5, 6, 7, 8, 20, 21}
    Blue distances: {9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}
    """
    RED_DISTANCES = {1, 2, 3, 4, 5, 6, 7, 8, 20, 21}

    graph = RamseyGraph(42)
    for i in range(1, 43):  # Original vertices 1-42
        for j in range(i+1, 43):
            new_i = i - 1
            new_j = j - 1
            diff = abs(j - i)
            dist = min(diff, 43 - diff)
            is_blue = dist not in RED_DISTANCES
            graph.set_edge(new_i, new_j, is_blue)

    return graph


def find_red_k5s(graph: RamseyGraph) -> list:
    """Find all red K5s in the graph."""
    n = graph.n
    k5s = []
    for combo in combinations(range(n), 5):
        all_red = True
        for i in range(5):
            for j in range(i+1, 5):
                if graph.get_edge(combo[i], combo[j]):  # If blue
                    all_red = False
                    break
            if not all_red:
                break
        if all_red:
            k5s.append(combo)
    return k5s


def greedy_edge_flip(graph: RamseyGraph, max_iters: int = 10000):
    """
    Greedy edge flipping to eliminate red K5s.
    At each step, flip the edge that eliminates the most red K5s
    without creating any blue K5s.
    """
    print("Starting greedy edge flip...")

    current = graph
    red_k5s = find_red_k5s(current)
    print(f"Initial: {len(red_k5s)} red K5s")

    iteration = 0
    while red_k5s and iteration < max_iters:
        # Find edges in red K5s
        edge_in_k5s = {}
        for k5 in red_k5s:
            for i in range(5):
                for j in range(i+1, 5):
                    e = (k5[i], k5[j])
                    if e not in edge_in_k5s:
                        edge_in_k5s[e] = 0
                    edge_in_k5s[e] += 1

        # Try flipping edges that appear in the most K5s
        best_edge = None
        best_reduction = 0
        best_new_blue = float('inf')

        # Sort edges by frequency
        sorted_edges = sorted(edge_in_k5s.items(), key=lambda x: -x[1])

        for (i, j), count in sorted_edges[:100]:  # Check top 100
            # Try flipping this edge
            test_graph = current.copy()
            test_graph.set_edge(i, j, True)  # Make blue

            new_red, new_blue = count_mono_k5(test_graph)

            if new_blue == 0:  # No new blue K5s
                reduction = len(red_k5s) - new_red
                if reduction > best_reduction:
                    best_reduction = reduction
                    best_edge = (i, j)
                    best_new_blue = new_blue

        if best_edge is None:
            print(f"No safe edge to flip at iteration {iteration}")
            break

        # Apply the best flip
        current.set_edge(best_edge[0], best_edge[1], True)
        red_k5s = find_red_k5s(current)

        iteration += 1
        if iteration % 10 == 0 or len(red_k5s) < 100:
            print(f"Iteration {iteration}: {len(red_k5s)} red K5s remaining")

        if len(red_k5s) == 0:
            print(f"\n*** SUCCESS at iteration {iteration}! ***")
            return current

    return current


def simulated_annealing_flip(graph: RamseyGraph, max_iters: int = 100000):
    """
    Simulated annealing to find edge flips that eliminate all K5s.
    """
    print("\nStarting simulated annealing...")

    current = graph.copy()
    red_k5, blue_k5 = count_mono_k5(current)
    current_score = red_k5 + blue_k5
    print(f"Initial: {red_k5} red, {blue_k5} blue K5s")

    best = current.copy()
    best_score = current_score

    temp = 10.0
    cooling = 0.9999

    n = current.n
    num_edges = n * (n - 1) // 2

    for iteration in range(max_iters):
        if best_score == 0:
            print(f"\n*** FOUND (5,5)-free K_42 at iteration {iteration}! ***")
            return best

        # Pick random edge
        i = random.randint(0, n-2)
        j = random.randint(i+1, n-1)

        # Flip it
        old_color = current.get_edge(i, j)
        current.set_edge(i, j, not old_color)

        new_red, new_blue = count_mono_k5(current)
        new_score = new_red + new_blue

        # Accept or reject
        if new_score <= current_score or random.random() < math.exp((current_score - new_score) / temp):
            current_score = new_score
            if new_score < best_score:
                best = current.copy()
                best_score = new_score
        else:
            # Revert
            current.set_edge(i, j, old_color)

        temp *= cooling

        if iteration % 10000 == 0:
            print(f"Iter {iteration}: current={current_score}, best={best_score}, temp={temp:.4f}")

    return best


def main():
    print("=" * 60)
    print("Eliminating red K5s from Cyclic(42)")
    print("=" * 60)

    graph = construct_cyclic42_no_blue_k5()
    red_k5, blue_k5 = count_mono_k5(graph)
    print(f"\nCyclic(42) with no-blue-K5 distances:")
    print(f"  Red K5s: {red_k5}")
    print(f"  Blue K5s: {blue_k5}")

    # Try greedy first
    print("\n" + "-" * 40)
    result = greedy_edge_flip(graph.copy(), max_iters=5000)
    red_k5, blue_k5 = count_mono_k5(result)
    print(f"After greedy: {red_k5} red, {blue_k5} blue K5s")

    if red_k5 == 0 and blue_k5 == 0:
        save_graph(result)
        return

    # Try simulated annealing
    print("\n" + "-" * 40)
    result = simulated_annealing_flip(graph.copy(), max_iters=200000)
    red_k5, blue_k5 = count_mono_k5(result)
    print(f"After SA: {red_k5} red, {blue_k5} blue K5s")

    if red_k5 == 0 and blue_k5 == 0:
        save_graph(result)


def save_graph(graph: RamseyGraph):
    """Save the (5,5)-free graph."""
    print("\n*** Saving (5,5)-free K_42! ***")
    with open("exoo42_verified.txt", "w") as f:
        f.write("# (5,5)-free 2-coloring of K_42\n")
        f.write("# Proves R(5,5) >= 43\n")
        for i in range(42):
            for j in range(i+1, 42):
                color = 1 if graph.get_edge(i, j) else 0
                f.write(f"{i} {j} {color}\n")
    print("Saved to exoo42_verified.txt")

    # Count edges
    blue = sum(1 for i in range(42) for j in range(i+1, 42) if graph.get_edge(i, j))
    red = 42*41//2 - blue
    print(f"Blue edges: {blue}, Red edges: {red}")


if __name__ == "__main__":
    random.seed(42)
    main()

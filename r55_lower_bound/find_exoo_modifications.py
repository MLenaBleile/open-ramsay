#!/usr/bin/env python3
"""
Find the exact edge modifications for Exoo's (5,5,42) construction.

From literature:
- Start with Cyclic(43) minus vertex 0
- Flip 16 edges from red to blue
- 15 are consecutive edges (i, i+1)
- 1 is the edge (10, 31) at distance 21

We search over C(41, 15) = 53 billion subsets of consecutive edges.
Too many to enumerate, so we use:
1. Constraint propagation from existing K5s
2. Simulated annealing over edge subsets
"""

import sys
import random
import math
from itertools import combinations
from typing import Set, Tuple, List, Optional

sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5


def cyclic42_base() -> RamseyGraph:
    """Cyclic(43) with vertex 0 removed."""
    BLUE_DISTANCES = {4, 5, 6, 9, 10, 11, 13, 16, 17}

    graph = RamseyGraph(42)
    for i_orig in range(1, 43):
        for j_orig in range(i_orig + 1, 43):
            i_new = i_orig - 1
            j_new = j_orig - 1
            diff = abs(j_orig - i_orig)
            dist = min(diff, 43 - diff)
            color = dist in BLUE_DISTANCES
            graph.set_edge(i_new, j_new, color)
    return graph


def find_k5_containing_edges(graph: RamseyGraph, edges: Set[Tuple[int,int]], color: bool) -> List[Tuple]:
    """Find all monochromatic K5s that contain at least one of the given edges."""
    k5s = []
    for v1 in range(42):
        for v2 in range(v1+1, 42):
            for v3 in range(v2+1, 42):
                for v4 in range(v3+1, 42):
                    for v5 in range(v4+1, 42):
                        vertices = [v1, v2, v3, v4, v5]
                        # Check if monochromatic
                        mono = True
                        first_color = graph.get_edge(v1, v2)
                        if first_color != color:
                            continue
                        for i in range(5):
                            for j in range(i+1, 5):
                                if graph.get_edge(vertices[i], vertices[j]) != color:
                                    mono = False
                                    break
                            if not mono:
                                break
                        if mono:
                            # Check if contains any target edge
                            for i in range(5):
                                for j in range(i+1, 5):
                                    e = (vertices[i], vertices[j]) if vertices[i] < vertices[j] else (vertices[j], vertices[i])
                                    if e in edges:
                                        k5s.append(tuple(vertices))
                                        break
                                else:
                                    continue
                                break
    return k5s


def search_modifications_sa(max_iter: int = 100000) -> Optional[Set[Tuple[int, int]]]:
    """Search for correct 15 consecutive edge modifications using simulated annealing."""
    # All consecutive edges (0-indexed)
    consecutive = [(i, i+1) for i in range(41)]

    # Fixed edge
    fixed = (10, 31)

    # Start with random 15 consecutive edges
    current = set(random.sample(consecutive, 15))

    def evaluate(mods: Set[Tuple[int, int]]) -> int:
        graph = cyclic42_base()
        # Apply fixed edge
        graph.set_edge(10, 31, True)  # Flip to blue
        # Apply modifications (flip red to blue)
        for i, j in mods:
            if not graph.get_edge(i, j):  # If red
                graph.set_edge(i, j, True)  # Make blue
        red_k5, blue_k5 = count_mono_k5(graph)
        return red_k5 + blue_k5

    current_score = evaluate(current)
    best = current.copy()
    best_score = current_score

    print(f"Initial score: {current_score}")

    temp = 5.0
    cooling = 0.9999

    for iteration in range(max_iter):
        if best_score == 0:
            print(f"\n*** FOUND SOLUTION at iteration {iteration}! ***")
            return best | {fixed}

        # Swap one edge
        edge_out = random.choice(list(current))
        available = set(consecutive) - current
        if not available:
            continue
        edge_in = random.choice(list(available))

        new_current = (current - {edge_out}) | {edge_in}
        new_score = evaluate(new_current)

        # Accept or reject
        if new_score < current_score or random.random() < math.exp((current_score - new_score) / temp):
            current = new_current
            current_score = new_score

            if new_score < best_score:
                best = current.copy()
                best_score = new_score

        temp *= cooling

        if iteration % 5000 == 0:
            print(f"Iter {iteration}: current={current_score}, best={best_score}, temp={temp:.4f}")

    return best | {fixed} if best_score == 0 else None


def search_contiguous_blocks(max_block_size: int = 20) -> Optional[Set[Tuple[int, int]]]:
    """Search assuming the 15 edges form a contiguous or near-contiguous block."""
    print("Trying contiguous blocks of 15 consecutive edges...")

    consecutive = [(i, i+1) for i in range(41)]

    # Try all starting positions for a block of 15
    for start in range(27):  # 41 - 15 + 1 = 27 positions
        mods = set(consecutive[start:start+15])

        graph = cyclic42_base()
        graph.set_edge(10, 31, True)
        for i, j in mods:
            if not graph.get_edge(i, j):
                graph.set_edge(i, j, True)

        red_k5, blue_k5 = count_mono_k5(graph)
        total = red_k5 + blue_k5

        if total == 0:
            print(f"  FOUND! Block starting at {start}")
            return mods | {(10, 31)}

        if total < 50:
            print(f"  Start {start}: {total} violations (promising)")

    print("No contiguous block works, trying with gaps...")
    return None


def search_pattern_based() -> Optional[Set[Tuple[int, int]]]:
    """Try patterns mentioned in literature hints."""
    patterns = [
        # Pattern 1: Every other edge starting at 0
        set([(2*i, 2*i+1) for i in range(15)]),
        # Pattern 2: Every other edge starting at 1
        set([(2*i+1, 2*i+2) for i in range(15) if 2*i+2 <= 41]),
        # Pattern 3: First 15
        set([(i, i+1) for i in range(15)]),
        # Pattern 4: Last 15
        set([(i, i+1) for i in range(26, 41)]),
        # Pattern 5: Middle 15
        set([(i, i+1) for i in range(13, 28)]),
        # Pattern 6: Spread evenly (every ~2.7)
        set([(int(i*41/15), int(i*41/15)+1) for i in range(15) if int(i*41/15)+1 <= 41]),
    ]

    print("Trying known patterns...")
    for idx, pattern in enumerate(patterns):
        if len(pattern) != 15:
            continue

        graph = cyclic42_base()
        graph.set_edge(10, 31, True)
        for i, j in pattern:
            if i < 42 and j < 42:
                if not graph.get_edge(i, j):
                    graph.set_edge(i, j, True)

        red_k5, blue_k5 = count_mono_k5(graph)
        total = red_k5 + blue_k5
        print(f"  Pattern {idx+1}: {total} violations")

        if total == 0:
            return pattern | {(10, 31)}

    return None


def main():
    print("=" * 60)
    print("Searching for Exoo(42) edge modifications")
    print("=" * 60)

    # First check base graph
    base = cyclic42_base()
    red_k5, blue_k5 = count_mono_k5(base)
    print(f"\nCyclic(42) base: {red_k5} red K5s, {blue_k5} blue K5s")

    # With just the fixed edge
    base.set_edge(10, 31, True)
    red_k5, blue_k5 = count_mono_k5(base)
    print(f"With edge (10,31) flipped: {red_k5} red K5s, {blue_k5} blue K5s")

    # Try pattern-based search first
    print("\n--- Pattern-based search ---")
    result = search_pattern_based()
    if result:
        print(f"\nFound via patterns: {sorted(result)}")
        return

    # Try contiguous blocks
    print("\n--- Contiguous block search ---")
    result = search_contiguous_blocks()
    if result:
        print(f"\nFound via contiguous: {sorted(result)}")
        return

    # Fall back to simulated annealing
    print("\n--- Simulated annealing search ---")
    for seed in range(5):
        print(f"\nTrying seed {seed}...")
        random.seed(seed)
        result = search_modifications_sa(max_iter=50000)
        if result:
            print(f"\nFOUND! Modifications: {sorted(result)}")

            # Verify
            graph = cyclic42_base()
            for i, j in result:
                graph.set_edge(i, j, True)
            red_k5, blue_k5 = count_mono_k5(graph)
            print(f"Verification: {red_k5} red K5s, {blue_k5} blue K5s")

            if red_k5 == 0 and blue_k5 == 0:
                print("\n*** SUCCESS! Graph is (5,5)-free! ***")
                # Save the graph
                with open("exoo42_found.txt", "w") as f:
                    f.write("# Exoo's (5,5,42) graph - modifications from Cyclic(42)\n")
                    f.write(f"# Edge modifications: {sorted(result)}\n")
                    f.write("# Edge format: i j color (0=red, 1=blue)\n")
                    for i in range(42):
                        for j in range(i+1, 42):
                            color = 1 if graph.get_edge(i, j) else 0
                            f.write(f"{i} {j} {color}\n")
                print("Saved to exoo42_found.txt")
            return

    print("\nDid not find solution in this run.")


if __name__ == "__main__":
    main()

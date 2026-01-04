#!/usr/bin/env python3
"""
Reconstruct Exoo's (5,5)-free K_42 from the literature.

Key insight from "Study of Exoo's Lower Bound for Ramsey number R(5,5)":
- Cyclic(43) colors edges by distance
- The 5-tuple (i, i+1, i+2, i+22, i+23) mod 43 forms a red K5 for each i
- All 43 red K5s share overlapping vertices
- Removing vertex 0 gives Exoo(42) which is (5,5)-free

The distances in the red K5 pattern are:
- d(i, i+1) = 1
- d(i, i+2) = 2
- d(i, i+22) = 21 (since min(22, 43-22) = 21)
- d(i, i+23) = 20 (since min(23, 43-23) = 20)
- d(i+1, i+22) = 21
- d(i+1, i+23) = 21
- d(i+2, i+22) = 20
- d(i+2, i+23) = 21
- d(i+22, i+23) = 1

So RED distances include: {1, 2, 20, 21}
The remaining distances {3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19} must be split
between red and blue such that neither forms a K5.
"""

import sys
sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free
from itertools import combinations


def find_k5s_with_vertices(graph: RamseyGraph, color: bool) -> list:
    """Find all monochromatic K5s and the vertices they contain."""
    n = graph.n
    k5s = []
    for combo in combinations(range(n), 5):
        # Check if all 10 edges have the same color
        all_same = True
        for i in range(5):
            for j in range(i+1, 5):
                if graph.get_edge(combo[i], combo[j]) != color:
                    all_same = False
                    break
            if not all_same:
                break
        if all_same:
            k5s.append(combo)
    return k5s


def cyclic43_red_k5_distances():
    """
    From the paper: (i, i+1, i+2, i+22, i+23) is a red K5.
    Compute all unique distances in this pattern.
    """
    # The 5 vertices in relative positions
    positions = [0, 1, 2, 22, 23]
    distances = set()

    for i in range(5):
        for j in range(i+1, 5):
            diff = abs(positions[j] - positions[i])
            dist = min(diff, 43 - diff)
            distances.add(dist)

    return distances


def construct_cyclic43_from_k5_pattern():
    """
    Construct Cyclic(43) such that (i, i+1, i+2, i+22, i+23) is red K5.

    The red distances must be exactly: {1, 2, 20, 21}
    All other distances (3-19) must be blue.
    """
    RED_DISTANCES = {1, 2, 20, 21}

    graph = RamseyGraph(43)
    for i in range(43):
        for j in range(i+1, 43):
            diff = abs(j - i)
            dist = min(diff, 43 - diff)
            # Red if distance in RED_DISTANCES, else Blue
            is_blue = dist not in RED_DISTANCES
            graph.set_edge(i, j, is_blue)

    return graph


def verify_red_k5_pattern(graph: RamseyGraph):
    """Verify that (i, i+1, i+2, i+22, i+23) forms a red K5."""
    for i in range(43):
        vertices = [(i + offset) % 43 for offset in [0, 1, 2, 22, 23]]
        # Check all 10 edges are red (is_blue = False)
        for a in range(5):
            for b in range(a+1, 5):
                v1, v2 = vertices[a], vertices[b]
                if v1 > v2:
                    v1, v2 = v2, v1
                if graph.get_edge(v1, v2):  # If blue
                    return False, i, (v1, v2)
    return True, None, None


def construct_exoo42():
    """
    Construct Exoo(42) = Cyclic(43) - vertex 0.
    This should be (5,5)-free.
    """
    cyclic43 = construct_cyclic43_from_k5_pattern()

    # Create K_42 by removing vertex 0
    # Relabel: old vertex i -> new vertex i-1 for i in 1..42
    exoo42 = RamseyGraph(42)
    for i in range(1, 43):
        for j in range(i+1, 43):
            new_i = i - 1
            new_j = j - 1
            color = cyclic43.get_edge(i, j)
            exoo42.set_edge(new_i, new_j, color)

    return exoo42


def main():
    print("=" * 60)
    print("Reconstructing Exoo's (5,5)-free K_42")
    print("=" * 60)

    # Step 1: Compute distances from the red K5 pattern
    print("\n[1] Red K5 pattern distances:")
    k5_distances = cyclic43_red_k5_distances()
    print(f"    Distances in (i, i+1, i+2, i+22, i+23): {sorted(k5_distances)}")

    # Step 2: Construct Cyclic(43)
    print("\n[2] Constructing Cyclic(43)...")
    cyclic43 = construct_cyclic43_from_k5_pattern()

    # Verify the red K5 pattern
    valid, fail_i, fail_edge = verify_red_k5_pattern(cyclic43)
    if valid:
        print("    ✓ Red K5 pattern (i, i+1, i+2, i+22, i+23) verified")
    else:
        print(f"    ✗ Pattern fails at i={fail_i}, edge {fail_edge}")
        return

    # Count K5s in Cyclic(43)
    red_k5, blue_k5 = count_mono_k5(cyclic43)
    print(f"    Cyclic(43): {red_k5} red K5s, {blue_k5} blue K5s")

    if blue_k5 != 0:
        print("    WARNING: Expected 0 blue K5s!")
        # Find blue K5s
        blue_k5s = find_k5s_with_vertices(cyclic43, True)
        print(f"    Blue K5s found: {blue_k5s[:5]}...")

    # Step 3: Construct Exoo(42)
    print("\n[3] Constructing Exoo(42) = Cyclic(43) - vertex 0...")
    exoo42 = construct_exoo42()

    # Verify (5,5)-free
    red_k5, blue_k5 = count_mono_k5(exoo42)
    print(f"    Exoo(42): {red_k5} red K5s, {blue_k5} blue K5s")

    if red_k5 == 0 and blue_k5 == 0:
        print("\n" + "=" * 60)
        print("*** SUCCESS! Exoo(42) is (5,5)-free! ***")
        print("*** This verifies R(5,5) >= 43 ***")
        print("=" * 60)

        # Save the graph
        save_exoo42(exoo42)
        return True
    else:
        print("\n    ✗ Exoo(42) is NOT (5,5)-free")

        # Try removing different vertices
        print("\n[4] Trying to remove different vertices from Cyclic(43)...")
        for remove_v in range(43):
            test_graph = RamseyGraph(42)
            # Map vertices: old v -> new v-1 if v > remove_v, else v
            old_to_new = {}
            new_idx = 0
            for v in range(43):
                if v != remove_v:
                    old_to_new[v] = new_idx
                    new_idx += 1

            for i in range(43):
                if i == remove_v:
                    continue
                for j in range(i+1, 43):
                    if j == remove_v:
                        continue
                    color = cyclic43.get_edge(i, j)
                    test_graph.set_edge(old_to_new[i], old_to_new[j], color)

            red_k5, blue_k5 = count_mono_k5(test_graph)
            if red_k5 == 0 and blue_k5 == 0:
                print(f"    ✓ Removing vertex {remove_v} gives (5,5)-free K_42!")
                save_exoo42(test_graph, f"exoo42_remove{remove_v}")
                return True
            elif red_k5 + blue_k5 < 10:
                print(f"    Vertex {remove_v}: {red_k5} red, {blue_k5} blue K5s")

        return False


def save_exoo42(graph: RamseyGraph, name: str = "exoo42"):
    """Save the verified Exoo(42) graph."""
    filename = f"{name}_verified.txt"
    with open(filename, "w") as f:
        f.write(f"# Exoo's (5,5)-free 2-coloring of K_42\n")
        f.write(f"# Proves R(5,5) >= 43\n")
        f.write(f"# Based on Exoo 1989: 'A lower bound for r(5,5)'\n")
        f.write(f"# Red distances: {{1, 2, 20, 21}}\n")
        f.write(f"# Blue distances: {{3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19}}\n")
        f.write(f"# Format: i j color (0=red, 1=blue)\n")
        for i in range(42):
            for j in range(i+1, 42):
                color = 1 if graph.get_edge(i, j) else 0
                f.write(f"{i} {j} {color}\n")
    print(f"    Saved to {filename}")

    # Also print statistics
    blue_edges = sum(1 for i in range(42) for j in range(i+1, 42) if graph.get_edge(i, j))
    red_edges = 42 * 41 // 2 - blue_edges
    print(f"    Blue edges: {blue_edges}, Red edges: {red_edges}")


if __name__ == "__main__":
    main()

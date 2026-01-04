#!/usr/bin/env python3
"""
Verify the (5,5)-free K_42 from the literature.

Source: GitHub gist by etherwalker containing K_43 graphs with only 2 K5s.
Removing vertex 0 (which is in both K5s) gives a (5,5)-free K_42.
"""

import sys
sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free

# K_43 adjacency matrix from GitHub gist (Graph 1)
# Monochromatic K5s: {0, 28, 29, 38, 2} and {0, 28, 29, 38, 11}
# Both contain vertex 0, so removing vertex 0 gives (5,5)-free K_42
K43_ADJACENCY = [
    "0000010100000001110101111100000111101101101",
    "0000100010000011101011111100011000110111011",
    "0000011000111100110101001101001000111001101",
    "0000100001111111000010111110100001000110011",
    "0101010000000010001111111100100111000011011",
    "1010100000000000011111111100011010011001101",
    "0010000110011110010101000011001101101111000",
    "1000001001010111010010010011101110001110010",
    "0100001001010110111101000011111000101010100",
    "0001000110110110010010110011110000111110000",
    "0011000001001100011111001001111101011101001",
    "0011001111001111101000001010000011011001010",
    "0011001000110010000010110110111111110010001",
    "0011001111110001111000100101000011010010100",
    "0101101111011001001000010000101110010011100",
    "1101000100010110101010111001100000000111111",
    "1110000010010101010101000110001010101001111",
    "1010011111100100101001100000111011001000010",
    "0100110010110111010100101010110010111000110",
    "1010111010100000101011000101010100001110110",
    "0101110101101001000100011010010110101010110",
    "1110111010100000110100000010110101000101011",
    "1101110001001101011000010101101101010101000",
    "1101110101001011000010100001011100110000101",
    "1111110000110001001010000010110101101001101",
    "1111110000001100100100100001011110010110011",
    "0001001111011000101011001000111100110101011",
    "0010001111100101000100110100111111100100101",
    "0001100111101011011001101011001100010001010",
    "0100010011101000011111011111001000010001011",
    "0110011110101010110000110111110011000001100",
    "1000101100101010000111111111100011000000101",
    "1000110100011110111010000101001101000111110",
    "1001101000111100010001101001001110011111010",
    "1110001011001000101010011011000000011111111",
    "0110010001111110001000110110110001101011100",
    "1010011111110000111110001000000001110100010",
    "1101001101100001000101100111000011101010111",
    "0101101111001111000110000100000011110100100",
    "1110111000110011100001101010111011110000000",
    "1010010010000111101110011001001110110110010",
    "0101100100010001111111000110110011101100100",
    "1111110000101001100001011111010100100100000",
]


def parse_k43_adjacency():
    """Parse the adjacency matrix into a RamseyGraph."""
    graph = RamseyGraph(43)
    for i in range(43):
        for j in range(43):
            if i < j:
                # 1 = blue edge, 0 = red edge
                is_blue = K43_ADJACENCY[i][j] == '1'
                graph.set_edge(i, j, is_blue)
    return graph


def extract_k42(k43_graph: RamseyGraph, remove_vertex: int = 0):
    """
    Extract a K_42 by removing the specified vertex.

    Args:
        k43_graph: The K_43 graph
        remove_vertex: Vertex to remove (default 0)

    Returns:
        K_42 graph with remaining vertices relabeled 0-41
    """
    k42 = RamseyGraph(42)

    # Map old vertices to new
    old_to_new = {}
    new_idx = 0
    for v in range(43):
        if v != remove_vertex:
            old_to_new[v] = new_idx
            new_idx += 1

    # Copy edges
    for i in range(43):
        if i == remove_vertex:
            continue
        for j in range(i + 1, 43):
            if j == remove_vertex:
                continue
            color = k43_graph.get_edge(i, j)
            k42.set_edge(old_to_new[i], old_to_new[j], color)

    return k42


def main():
    print("=" * 60)
    print("Verifying (5,5)-free K_42 from Literature")
    print("=" * 60)
    print()
    print("Source: GitHub gist by etherwalker")
    print("  https://gist.github.com/etherwalker/8d64fa0a1cc1dd508f75bf651aaec873")
    print()

    # Parse the K_43 adjacency matrix
    print("[1] Parsing K_43 adjacency matrix...")
    k43 = parse_k43_adjacency()
    red_k5, blue_k5 = count_mono_k5(k43)
    print(f"    K_43: {red_k5} red K5s, {blue_k5} blue K5s")
    print(f"    Expected: 2 monochromatic K5s (both contain vertex 0)")
    print()

    # Extract K_42 by removing vertex 0
    print("[2] Extracting K_42 by removing vertex 0...")
    k42 = extract_k42(k43, remove_vertex=0)

    # Verify (5,5)-free
    print("[3] Verifying K_42 is (5,5)-free...")
    red_k5, blue_k5 = count_mono_k5(k42)
    print(f"    K_42: {red_k5} red K5s, {blue_k5} blue K5s")
    print()

    if red_k5 == 0 and blue_k5 == 0:
        print("=" * 60)
        print("*** SUCCESS! K_42 is (5,5)-free! ***")
        print("*** This verifies R(5,5) >= 43 ***")
        print("=" * 60)

        # Save the graph
        save_verified_k42(k42)

        # Also verify with exhaustive check
        print()
        print("[4] Running exhaustive verification...")
        is_valid, counterexample = verify_k5_free(k42)
        if is_valid:
            print("    ✓ Exhaustive check confirms: NO monochromatic K5")
        else:
            print(f"    ✗ Found K5: {counterexample}")

        return True
    else:
        print("ERROR: K_42 is NOT (5,5)-free!")
        return False


def save_verified_k42(graph: RamseyGraph):
    """Save the verified (5,5)-free K_42 graph."""
    filename = "exoo42_from_literature.txt"
    with open(filename, "w") as f:
        f.write("# (5,5)-free 2-coloring of K_42\n")
        f.write("# Proves R(5,5) >= 43\n")
        f.write("#\n")
        f.write("# Source: GitHub gist by etherwalker\n")
        f.write("# https://gist.github.com/etherwalker/8d64fa0a1cc1dd508f75bf651aaec873\n")
        f.write("#\n")
        f.write("# Construction: K_43 with only 2 monochromatic K5s, minus vertex 0\n")
        f.write("# Original K5s: {0, 28, 29, 38, 2} and {0, 28, 29, 38, 11}\n")
        f.write("#\n")
        f.write("# Format: i j color (0=red, 1=blue)\n")
        f.write("#\n")

        for i in range(42):
            for j in range(i + 1, 42):
                color = 1 if graph.get_edge(i, j) else 0
                f.write(f"{i} {j} {color}\n")

    print(f"    Saved to {filename}")

    # Statistics
    blue_edges = sum(1 for i in range(42) for j in range(i+1, 42) if graph.get_edge(i, j))
    red_edges = 42 * 41 // 2 - blue_edges
    print(f"    Blue edges: {blue_edges}")
    print(f"    Red edges: {red_edges}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Find the correct distance coloring for Cyclic(43) that gives:
- Exactly 43 red K5s of the form (i, i+1, i+2, i+22, i+23)
- Exactly 0 blue K5s

The red K5 pattern determines that red distances must include {1, 2, 20, 21}.
We need to find the complete partition of {1..21} into red and blue.
"""

import sys
from itertools import combinations, product
sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5


def distance_k5_check(blue_distances: set) -> int:
    """
    Count blue K5s in Cyclic(43) with given blue distance set.
    Uses the pattern that all K5s in a cyclic graph have specific distance patterns.
    """
    n = 43
    k5_count = 0

    # Check all 5-subsets
    for v1 in range(n):
        for v2 in range(v1+1, n):
            for v3 in range(v2+1, n):
                for v4 in range(v3+1, n):
                    for v5 in range(v4+1, n):
                        vertices = [v1, v2, v3, v4, v5]
                        # Check if all 10 edges are blue
                        all_blue = True
                        for i in range(5):
                            for j in range(i+1, 5):
                                diff = abs(vertices[j] - vertices[i])
                                dist = min(diff, n - diff)
                                if dist not in blue_distances:
                                    all_blue = False
                                    break
                            if not all_blue:
                                break
                        if all_blue:
                            k5_count += 1

    return k5_count


def verify_red_k5_count(red_distances: set) -> int:
    """Count red K5s to verify the pattern."""
    n = 43
    k5_count = 0

    for v1 in range(n):
        for v2 in range(v1+1, n):
            for v3 in range(v2+1, n):
                for v4 in range(v3+1, n):
                    for v5 in range(v4+1, n):
                        vertices = [v1, v2, v3, v4, v5]
                        all_red = True
                        for i in range(5):
                            for j in range(i+1, 5):
                                diff = abs(vertices[j] - vertices[i])
                                dist = min(diff, n - diff)
                                if dist not in red_distances:
                                    all_red = False
                                    break
                            if not all_red:
                                break
                        if all_red:
                            k5_count += 1

    return k5_count


def find_valid_partition():
    """
    Find a partition of {1..21} into red and blue such that:
    - Red contains {1, 2, 20, 21} (forced)
    - Blue K5 count = 0
    """
    all_distances = set(range(1, 22))
    forced_red = {1, 2, 20, 21}
    remaining = all_distances - forced_red  # {3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19}

    print(f"All distances: {sorted(all_distances)}")
    print(f"Forced red: {sorted(forced_red)}")
    print(f"Remaining to partition: {sorted(remaining)}")
    print(f"Number of partitions to check: {2**len(remaining)} = {2**17}")
    print()

    best_blue_k5 = float('inf')
    best_partition = None

    # Check all 2^17 = 131072 partitions
    count = 0
    for bits in range(2**len(remaining)):
        remaining_list = sorted(remaining)
        additional_red = set()
        for i, d in enumerate(remaining_list):
            if bits & (1 << i):
                additional_red.add(d)

        red_distances = forced_red | additional_red
        blue_distances = all_distances - red_distances

        blue_k5 = distance_k5_check(blue_distances)

        if blue_k5 < best_blue_k5:
            best_blue_k5 = blue_k5
            best_partition = (sorted(red_distances), sorted(blue_distances))
            print(f"Better partition found! Blue K5s = {blue_k5}")
            print(f"  Red:  {best_partition[0]}")
            print(f"  Blue: {best_partition[1]}")

        if blue_k5 == 0:
            print(f"\n*** FOUND VALID PARTITION! ***")
            print(f"Red distances:  {sorted(red_distances)}")
            print(f"Blue distances: {sorted(blue_distances)}")

            # Verify red K5 count
            red_k5 = verify_red_k5_count(red_distances)
            print(f"Red K5 count: {red_k5}")
            return red_distances, blue_distances

        count += 1
        if count % 10000 == 0:
            print(f"Checked {count}/131072 partitions, best blue K5s = {best_blue_k5}")

    print(f"\nNo valid partition found. Best had {best_blue_k5} blue K5s")
    print(f"Best partition:")
    print(f"  Red:  {best_partition[0]}")
    print(f"  Blue: {best_partition[1]}")
    return None, None


def main():
    print("=" * 60)
    print("Finding correct Cyclic(43) distance coloring")
    print("=" * 60)
    print()

    red, blue = find_valid_partition()

    if red and blue:
        print("\n" + "=" * 60)
        print("Constructing and verifying Exoo(42)")
        print("=" * 60)

        # Construct Cyclic(43) with found coloring
        blue_set = set(blue)
        graph43 = RamseyGraph(43)
        for i in range(43):
            for j in range(i+1, 43):
                diff = abs(j - i)
                dist = min(diff, 43 - diff)
                is_blue = dist in blue_set
                graph43.set_edge(i, j, is_blue)

        red_k5, blue_k5 = count_mono_k5(graph43)
        print(f"Cyclic(43): {red_k5} red K5s, {blue_k5} blue K5s")

        # Remove vertex 0 to get Exoo(42)
        graph42 = RamseyGraph(42)
        for i in range(1, 43):
            for j in range(i+1, 43):
                graph42.set_edge(i-1, j-1, graph43.get_edge(i, j))

        red_k5, blue_k5 = count_mono_k5(graph42)
        print(f"Exoo(42): {red_k5} red K5s, {blue_k5} blue K5s")

        if red_k5 == 0 and blue_k5 == 0:
            print("\n*** SUCCESS! Exoo(42) is (5,5)-free! ***")
            print("*** This verifies R(5,5) >= 43 ***")

            # Save
            with open("exoo42_verified.txt", "w") as f:
                f.write(f"# Exoo's (5,5)-free K_42\n")
                f.write(f"# Red distances: {sorted(red)}\n")
                f.write(f"# Blue distances: {sorted(blue)}\n")
                for i in range(42):
                    for j in range(i+1, 42):
                        color = 1 if graph42.get_edge(i, j) else 0
                        f.write(f"{i} {j} {color}\n")
            print("Saved to exoo42_verified.txt")


if __name__ == "__main__":
    main()

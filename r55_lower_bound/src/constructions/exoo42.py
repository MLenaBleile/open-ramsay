"""
Exoo's (5,5,42) graph construction.

Geoffrey Exoo proved R(5,5) >= 43 in 1989 by constructing a (5,5)-free
2-coloring of K_42.

The construction is based on a cyclic graph on 43 vertices:
1. Cyclic(43): Color edges by distance, with specific red/blue distances
2. Delete vertex 0 to get 42 vertices
3. Change 16 specific edges from red to blue

Blue distances in Cyclic(43): {4, 5, 6, 9, 10, 11, 13, 16, 17}
Red distances in Cyclic(43): {1, 2, 3, 7, 8, 12, 14, 15, 18, 19, 20, 21}

Edge modifications for Exoo(42): 15 consecutive pairs + edge (11, 32)

References:
- Exoo, G. "A lower bound for R(5,5)", J. Graph Theory 13 (1989) 97-98
- McKay & Radziszowski found 656 such graphs (328 + complements)
"""

import sys
from typing import Optional, Set, List, Tuple
from itertools import combinations

sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free


# Cyclic(43) color assignments
# Blue distances (True)
CYCLIC43_BLUE_DISTANCES = {4, 5, 6, 9, 10, 11, 13, 16, 17}
# Red distances (False)
CYCLIC43_RED_DISTANCES = {1, 2, 3, 7, 8, 12, 14, 15, 18, 19, 20, 21}


def cyclic43_distance(i: int, j: int) -> int:
    """
    Compute the cyclic distance between vertices i and j in Cyclic(43).

    Distance is the length of the shorter arc on a circle of 43 points.

    Args:
        i, j: Vertex indices (0 to 42 in original, 1 to 42 after vertex 0 removal)

    Returns:
        Distance in range [1, 21]
    """
    diff = abs(j - i)
    return min(diff, 43 - diff)


def cyclic43_coloring() -> RamseyGraph:
    """
    Construct the Cyclic(43) graph.

    This is the base graph before vertex removal and edge modifications.

    Returns:
        RamseyGraph on 43 vertices with cyclic coloring
    """
    graph = RamseyGraph(43)

    for i in range(43):
        for j in range(i + 1, 43):
            dist = cyclic43_distance(i, j)
            # Blue if distance is in blue set
            color = dist in CYCLIC43_BLUE_DISTANCES
            graph.set_edge(i, j, color)

    return graph


def cyclic42_base() -> RamseyGraph:
    """
    Construct Cyclic(43) with vertex 0 removed.

    This is the intermediate step before edge color modifications.
    Vertices are numbered 1-42 (but stored as 0-41 internally).

    Returns:
        RamseyGraph on 42 vertices
    """
    graph = RamseyGraph(42)

    # Original vertices 1-42, mapped to 0-41
    for i_orig in range(1, 43):
        for j_orig in range(i_orig + 1, 43):
            i_new = i_orig - 1  # Map to 0-indexed
            j_new = j_orig - 1

            dist = cyclic43_distance(i_orig, j_orig)
            color = dist in CYCLIC43_BLUE_DISTANCES
            graph.set_edge(i_new, j_new, color)

    return graph


def exoo42_graph(edge_modifications: Optional[Set[Tuple[int, int]]] = None) -> RamseyGraph:
    """
    Construct Exoo's (5,5,42) graph.

    If edge_modifications is None, uses a default set of modifications
    based on the literature description.

    Args:
        edge_modifications: Set of (i, j) edges to flip from red to blue.
                          Vertices are 0-indexed (0-41).

    Returns:
        RamseyGraph that should be (5,5)-free
    """
    graph = cyclic42_base()

    if edge_modifications is None:
        # Default modification based on literature hints:
        # - 15 consecutive edges
        # - Edge between original vertices 11 and 32 (distance 21)
        #
        # The edge (11, 32) in original numbering is (10, 31) in 0-indexed
        edge_modifications = get_candidate_modifications()

    for i, j in edge_modifications:
        if i > j:
            i, j = j, i
        current_color = graph.get_edge(i, j)
        # Flip from red (False) to blue (True)
        if not current_color:
            graph.set_edge(i, j, True)

    return graph


def get_candidate_modifications() -> Set[Tuple[int, int]]:
    """
    Get candidate edge modifications for Exoo(42).

    Based on literature:
    - 15 consecutive edges become blue
    - Edge (11, 32) in original numbering becomes blue

    The edge (11, 32) corresponds to (10, 31) in 0-indexed coordinates.

    Returns:
        Set of edges to modify
    """
    modifications = set()

    # The edge 11-32 (original) = 10-31 (0-indexed)
    modifications.add((10, 31))

    # Need to find which 15 consecutive edges to flip
    # Based on hints, edges 4-5 and 41-42 (original) are mentioned as blue
    # In 0-indexed: 3-4 and 40-41
    #
    # Let's try a pattern that includes these
    # We need 15 consecutive edges from the 41 available
    # These are edges (i, i+1) where i ranges from 0 to 40 (original 1-2 to 41-42)

    # Candidate pattern: skip some edges in a regular way
    # Based on the fact that the construction is "almost" cyclic
    # Try: edges that would eliminate red K5s

    # First, let's try all 41 consecutive edges and see what happens
    # Actually, we're told only 15 are changed. Let's start with
    # edges that seem to be mentioned: around 4-5, 41-42

    # Trial: 15 edges spread across the cycle
    # Based on pattern hints, try evenly spaced or specific pattern
    # Let's try: 15 edges near one section

    # Alternative interpretation: the 15 edges might be:
    # 3-4, 4-5, 5-6, 8-9, 9-10, 10-11, 12-13, 15-16, 16-17
    # and 27-28, 28-29, 29-30, 31-32, 39-40, 40-41 (in 0-indexed)
    # This is just a guess - we need to verify

    # For now, return a minimal set for testing
    return modifications


def find_exoo42_modifications() -> Optional[Set[Tuple[int, int]]]:
    """
    Search for the correct edge modifications to make Exoo(42) (5,5)-free.

    We know:
    1. There are 16 modifications total
    2. 15 are consecutive edges (form: (i, i+1))
    3. 1 is edge (10, 31) in 0-indexed = distance 21

    We need to find which 15 of the 41 consecutive edges to flip.

    Returns:
        Set of modifications that result in (5,5)-free graph, or None
    """
    # The edge (10, 31) is fixed
    fixed_edge = (10, 31)

    # Get all consecutive edges (41 total)
    consecutive_edges = [(i, i + 1) for i in range(41)]

    # We need exactly 15 of these
    # This is C(41, 15) = 53 billion - too many to enumerate

    # Use a smarter approach: start with the base graph and analyze
    # which red K5s exist, then find modifications that eliminate them

    base = cyclic42_base()
    base.set_edge(10, 31, True)  # Apply the fixed modification

    red_k5_count, blue_k5_count = count_mono_k5(base)
    print(f"Base (with edge 10-31 flipped): {red_k5_count} red K5s, {blue_k5_count} blue K5s")

    if red_k5_count == 0 and blue_k5_count == 0:
        return {fixed_edge}

    # Try local search to find remaining modifications
    return search_modifications_local(base, consecutive_edges, 15)


def search_modifications_local(
    base_graph: RamseyGraph,
    candidate_edges: List[Tuple[int, int]],
    num_to_flip: int
) -> Optional[Set[Tuple[int, int]]]:
    """
    Local search for edge modifications.

    Use simulated annealing to find a subset of candidate_edges
    that when flipped (from red to blue) results in (5,5)-free graph.
    """
    import random
    import math

    # Start with random subset
    current = set(random.sample(candidate_edges, min(num_to_flip, len(candidate_edges))))

    def evaluate(modifications: Set[Tuple[int, int]]) -> int:
        graph = base_graph.copy()
        for i, j in modifications:
            if not graph.get_edge(i, j):  # Only flip red edges
                graph.set_edge(i, j, True)
        red_k5, blue_k5 = count_mono_k5(graph)
        return red_k5 + blue_k5

    current_score = evaluate(current)
    best = current.copy()
    best_score = current_score

    temp = 10.0
    cooling = 0.995

    for iteration in range(50000):
        if best_score == 0:
            print(f"Found solution at iteration {iteration}")
            return best

        # Try a modification: swap one edge in for one edge out
        if current and random.random() < 0.5:
            # Remove one edge
            edge_out = random.choice(list(current))
            new_current = current - {edge_out}

            # Add a different edge
            available = set(candidate_edges) - new_current
            if available:
                edge_in = random.choice(list(available))
                new_current.add(edge_in)
        else:
            # Add or remove an edge
            if len(current) < num_to_flip:
                available = set(candidate_edges) - current
                if available:
                    edge_in = random.choice(list(available))
                    new_current = current | {edge_in}
                else:
                    new_current = current
            else:
                if current:
                    edge_out = random.choice(list(current))
                    new_current = current - {edge_out}
                else:
                    new_current = current

        new_score = evaluate(new_current)

        # Accept or reject
        if new_score <= current_score or random.random() < math.exp((current_score - new_score) / temp):
            current = new_current
            current_score = new_score

            if new_score < best_score:
                best = current.copy()
                best_score = new_score
                print(f"Iteration {iteration}: best score = {best_score}")

        temp *= cooling

        if iteration % 10000 == 0:
            print(f"Iteration {iteration}: current = {current_score}, best = {best_score}, temp = {temp:.4f}")

    print(f"Search completed. Best score: {best_score}")
    return best if best_score == 0 else None


def cyclic43_coloring_inverted() -> RamseyGraph:
    """
    Construct Cyclic(43) with inverted colors (for testing).
    """
    graph = RamseyGraph(43)

    for i in range(43):
        for j in range(i + 1, 43):
            dist = cyclic43_distance(i, j)
            # Invert: Red if distance is in blue set
            color = dist in CYCLIC43_RED_DISTANCES
            graph.set_edge(i, j, color)

    return graph


def verify_known_construction():
    """
    Verify the known facts about Cyclic(43) and Exoo(42).
    """
    print("=== Verifying Cyclic(43) (original) ===")
    cyclic43 = cyclic43_coloring()
    red_k5, blue_k5 = count_mono_k5(cyclic43)
    print(f"Cyclic(43): {red_k5} red K5s, {blue_k5} blue K5s")

    print("\n=== Verifying Cyclic(43) (inverted colors) ===")
    cyclic43_inv = cyclic43_coloring_inverted()
    red_k5, blue_k5 = count_mono_k5(cyclic43_inv)
    print(f"Cyclic(43) inverted: {red_k5} red K5s, {blue_k5} blue K5s")

    # Check if inverted has 0 blue K5s (as paper claims)
    if blue_k5 == 0:
        print("  -> Inverted version has 0 blue K5s - this matches the paper!")
        print("  -> Using inverted colors is correct")

    print("\n=== Verifying Cyclic(42) base ===")
    cyclic42 = cyclic42_base()
    red_k5, blue_k5 = count_mono_k5(cyclic42)
    print(f"Cyclic(42) base: {red_k5} red K5s, {blue_k5} blue K5s")

    print("\n=== Testing edge (10,31) modification ===")
    test_graph = cyclic42_base()
    test_graph.set_edge(10, 31, True)
    red_k5, blue_k5 = count_mono_k5(test_graph)
    print(f"With edge (10,31) flipped: {red_k5} red K5s, {blue_k5} blue K5s")

    return cyclic43, cyclic42


if __name__ == "__main__":
    verify_known_construction()

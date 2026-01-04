"""
Paley graph construction.

For prime q ≡ 1 (mod 4), the Paley graph P(q) is:
- Self-complementary
- Strongly regular with parameters (q, (q-1)/2, (q-5)/4, (q-1)/4)
- Known to be (5,5)-free for q ≤ 37

For prime q ≡ 3 (mod 4), we use the standard Paley construction where
edge (i, j) is colored based on whether (j - i) mod q is a quadratic residue.

IMPORTANT CLARIFICATION:
- The Paley graph P(37) is (5,5)-free, proving R(5,5) ≥ 38
- The Paley graph P(41) is NOT (5,5)-free
- The lower bound R(5,5) ≥ 43 comes from a DIFFERENT construction
  (specifically, a 42-vertex circulant graph found computationally)
- We must NOT assume P(43) is (5,5)-free - it is NOT.

This file implements the standard Paley construction for verification
and as a building block for other constructions.
"""

from typing import Set
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph


def is_quadratic_residue(a: int, p: int) -> bool:
    """
    Check if a is a quadratic residue modulo p.

    Uses Euler's criterion: a is a QR mod p iff a^((p-1)/2) ≡ 1 (mod p)

    Args:
        a: The number to check (will be reduced mod p)
        p: An odd prime

    Returns:
        True if a is a quadratic residue mod p, False otherwise
    """
    a = a % p
    if a == 0:
        return False  # 0 is not considered a QR for our purposes

    # Euler's criterion
    return pow(a, (p - 1) // 2, p) == 1


def quadratic_residues(p: int) -> Set[int]:
    """
    Compute the set of quadratic residues modulo p.

    Args:
        p: An odd prime

    Returns:
        Set of non-zero quadratic residues mod p
    """
    qr = set()
    for a in range(1, p):
        if is_quadratic_residue(a, p):
            qr.add(a)
    return qr


def is_prime(n: int) -> bool:
    """Check if n is prime."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def paley_coloring(p: int) -> RamseyGraph:
    """
    Construct the Paley graph coloring on p vertices.

    For prime p, we color edge (i, j) based on whether (i - j) mod p
    is a quadratic residue.

    For p ≡ 1 (mod 4): The graph is self-complementary (symmetric QR set)
    For p ≡ 3 (mod 4): We use the convention that edge (i,j) is red if
                        (j - i) mod p is a quadratic residue.

    Note: For p ≡ 3 (mod 4), -1 is NOT a QR, so (i-j) and (j-i) have
    opposite QR status. We pick one consistently.

    Args:
        p: An odd prime

    Returns:
        RamseyGraph with Paley coloring

    Raises:
        ValueError: If p is not an odd prime
    """
    if not is_prime(p):
        raise ValueError(f"{p} is not prime")
    if p == 2:
        raise ValueError("Paley graph requires odd prime")

    graph = RamseyGraph(p)
    qr = quadratic_residues(p)

    for i in range(p):
        for j in range(i + 1, p):
            # Compute (j - i) mod p
            diff = (j - i) % p

            # Edge is blue (True) if diff is a quadratic residue
            # Edge is red (False) if diff is a non-residue
            color = diff in qr
            graph.set_edge(i, j, color)

    return graph


def paley_coloring_symmetric(p: int) -> RamseyGraph:
    """
    Construct a symmetric Paley-like coloring for any prime p.

    For p ≡ 1 (mod 4): Same as paley_coloring (already symmetric)
    For p ≡ 3 (mod 4): We use min(d, p-d) to make it symmetric

    This ensures that if (i,j) is red, then (j,i) is also red,
    which is required for undirected graphs.

    Args:
        p: An odd prime

    Returns:
        RamseyGraph with symmetric Paley-like coloring
    """
    if not is_prime(p):
        raise ValueError(f"{p} is not prime")
    if p == 2:
        raise ValueError("Paley graph requires odd prime")

    graph = RamseyGraph(p)
    qr = quadratic_residues(p)

    for i in range(p):
        for j in range(i + 1, p):
            # Use the smaller of (j-i) and (i-j) = p - (j-i)
            diff = j - i
            min_diff = min(diff, p - diff)

            # Edge is blue if min_diff is a QR
            color = min_diff in qr
            graph.set_edge(i, j, color)

    return graph


def verify_paley_properties(p: int) -> dict:
    """
    Verify properties of the Paley graph on p vertices.

    Args:
        p: An odd prime

    Returns:
        Dictionary with:
        - 'n': number of vertices
        - 'p_mod_4': p mod 4
        - 'num_qr': number of quadratic residues
        - 'red_edges': count of red edges
        - 'blue_edges': count of blue edges
        - 'is_balanced': whether red ≈ blue
        - 'degrees': list of (red_degree, blue_degree) for each vertex
    """
    graph = paley_coloring(p)
    qr = quadratic_residues(p)

    degrees = []
    for v in range(p):
        degrees.append((graph.red_degree(v), graph.blue_degree(v)))

    return {
        'n': p,
        'p_mod_4': p % 4,
        'num_qr': len(qr),
        'red_edges': graph.count_red_edges(),
        'blue_edges': graph.count_blue_edges(),
        'is_balanced': abs(graph.count_red_edges() - graph.count_blue_edges()) <= p,
        'degrees': degrees,
        'all_degrees_equal': len(set(degrees)) == 1,
    }


def get_paley_43() -> RamseyGraph:
    """
    Get the Paley graph on 43 vertices.

    WARNING: P(43) is NOT (5,5)-free! The R(5,5) ≥ 43 bound comes from
    a different construction (circulant graph on 42 vertices).

    This function is kept for testing and comparison purposes.

    Returns:
        RamseyGraph representing P(43)
    """
    return paley_coloring(43)


def get_best_paley_k5_free() -> RamseyGraph:
    """
    Get the largest Paley graph that is (5,5)-free.

    P(37) is the largest Paley graph verified to be (5,5)-free.
    This gives R(5,5) ≥ 38 from the Paley construction alone.

    Returns:
        RamseyGraph representing P(37)
    """
    return paley_coloring(37)


def find_k5_free_paley_graphs() -> list[int]:
    """
    Find all primes p ≤ 50 for which P(p) is (5,5)-free.

    Returns:
        List of primes for which the Paley graph is (5,5)-free
    """
    from src.core.clique_checker import verify_k5_free

    k5_free_primes = []
    for p in [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]:
        if is_prime(p):
            graph = paley_coloring(p)
            is_valid, _ = verify_k5_free(graph)
            if is_valid:
                k5_free_primes.append(p)
    return k5_free_primes


def extend_paley_to_n(p: int, n: int) -> RamseyGraph:
    """
    Extend the Paley graph P(p) to n vertices.

    For n > p, we add vertices p, p+1, ..., n-1 and need to color
    edges from these new vertices to all existing vertices.

    Strategy: Use cyclic extension - for new vertex v and existing
    vertex u, color edge (u, v) based on some pattern.

    Args:
        p: The prime for the base Paley graph
        n: Target number of vertices (n >= p)

    Returns:
        RamseyGraph with n vertices, first p forming Paley graph
    """
    if n < p:
        raise ValueError(f"n ({n}) must be >= p ({p})")

    base = paley_coloring(p)

    if n == p:
        return base

    # Create new graph with n vertices
    graph = RamseyGraph(n)

    # Copy the Paley graph for vertices 0..p-1
    for i in range(p):
        for j in range(i + 1, p):
            graph.set_edge(i, j, base.get_edge(i, j))

    # For new vertices, we need a coloring strategy
    # Default: use cyclic pattern based on vertex indices
    qr = quadratic_residues(p)

    for v in range(p, n):
        for u in range(v):
            if u < p:
                # Edge from original vertex to new vertex
                # Use (v - u) mod p to determine color
                diff = (v - u) % p
                if diff == 0:
                    diff = 1  # Avoid 0
                color = diff in qr
            else:
                # Edge between two new vertices
                # Use simple alternating pattern
                diff = (v - u) % p
                if diff == 0:
                    diff = 1
                color = diff in qr
            graph.set_edge(u, v, color)

    return graph

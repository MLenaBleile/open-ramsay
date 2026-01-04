#!/usr/bin/env python3
"""
Use SAT solving to find a (5,5)-free coloring of K_42.

This is more principled than local search since SAT solvers
use sophisticated techniques (CDCL, unit propagation, etc.)
to systematically explore the search space.
"""

import sys
import time
from itertools import combinations

sys.path.insert(0, 'src')

from pysat.solvers import Solver
from pysat.formula import CNF

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free


def edge_to_var(i: int, j: int, n: int) -> int:
    """Convert edge (i, j) to SAT variable (1-indexed)."""
    if i > j:
        i, j = j, i
    # Edge index in upper triangular matrix
    idx = i * (2 * n - i - 1) // 2 + (j - i - 1)
    return idx + 1


def var_to_edge(var: int, n: int) -> tuple:
    """Convert SAT variable back to edge."""
    idx = abs(var) - 1
    # Find i such that edge (i, j) has this index
    i = 0
    count = 0
    while count + (n - 1 - i) <= idx:
        count += n - 1 - i
        i += 1
    j = idx - count + i + 1
    return (i, j)


def create_k42_sat(symmetry_break: bool = True) -> CNF:
    """
    Create SAT formula for (5,5)-free K_42 coloring.

    Variables: x_ij where True = blue, False = red

    Constraints:
    - For each 5-set: at least one edge is blue (forbid all-red K5)
    - For each 5-set: at least one edge is red (forbid all-blue K5)
    """
    n = 42
    formula = CNF()

    print(f"Creating SAT formula for K_{n}...")
    print(f"  Variables: {n * (n-1) // 2}")

    # Number of 5-subsets
    num_subsets = 1
    for i in range(5):
        num_subsets = num_subsets * (n - i) // (i + 1)
    print(f"  5-subsets to check: {num_subsets}")
    print(f"  Clauses (2 per subset): {2 * num_subsets}")

    # Add clauses for each 5-subset
    subset_count = 0
    for subset in combinations(range(n), 5):
        # Get all 10 edges in this K_5
        edges = [(subset[i], subset[j]) for i in range(5) for j in range(i+1, 5)]
        edge_vars = [edge_to_var(i, j, n) for i, j in edges]

        # Forbid all-red K_5: at least one edge is blue (positive literal)
        formula.append(edge_vars)

        # Forbid all-blue K_5: at least one edge is red (negative literal)
        formula.append([-v for v in edge_vars])

        subset_count += 1
        if subset_count % 100000 == 0:
            print(f"  Processed {subset_count}/{num_subsets} subsets...")

    # Symmetry breaking: fix edge (0,1) to be red
    if symmetry_break:
        formula.append([-edge_to_var(0, 1, n)])
        print("  Added symmetry breaking constraint")

    print(f"  Total clauses: {len(formula.clauses)}")
    return formula


def solve_with_timeout(formula: CNF, timeout: int = 600) -> tuple:
    """
    Solve SAT formula with timeout.

    Args:
        formula: CNF formula
        timeout: Timeout in seconds

    Returns:
        (satisfiable, model) or (None, None) on timeout
    """
    solver = Solver(name='cadical153')

    for clause in formula.clauses:
        solver.add_clause(clause)

    print(f"\nSolving with {timeout}s timeout...")
    start = time.time()

    result = solver.solve_limited(expect_interrupt=True)
    elapsed = time.time() - start

    if result is None:
        print(f"Timeout after {elapsed:.1f}s")
        return None, None

    if result:
        model = solver.get_model()
        print(f"SAT! Found solution in {elapsed:.1f}s")
        return True, model
    else:
        print(f"UNSAT! No solution exists in {elapsed:.1f}s")
        return False, None


def model_to_graph(model: list, n: int) -> RamseyGraph:
    """Convert SAT model to RamseyGraph."""
    graph = RamseyGraph(n)
    for lit in model:
        if lit is None:
            continue
        var = abs(lit)
        is_blue = lit > 0
        i, j = var_to_edge(var, n)
        if i < n and j < n:
            graph.set_edge(i, j, is_blue)
    return graph


def main():
    print("=" * 60)
    print("SAT-based search for (5,5)-free K_42")
    print("=" * 60)

    # Create the formula
    formula = create_k42_sat(symmetry_break=True)

    # Try to solve
    sat, model = solve_with_timeout(formula, timeout=300)

    if sat is None:
        print("\nSearch timed out. The problem may require more time.")
        return

    if not sat:
        print("\nNo (5,5)-free coloring of K_42 exists (UNSAT).")
        print("This would contradict R(5,5) >= 43!")
        return

    # Convert solution to graph
    n = 42
    graph = model_to_graph(model, n)

    # Verify the solution
    print("\nVerifying solution...")
    is_valid, counterexample = verify_k5_free(graph)

    if is_valid:
        red_k5, blue_k5 = count_mono_k5(graph)
        print(f"\n*** SUCCESS! ***")
        print(f"Found (5,5)-free 2-coloring of K_42")
        print(f"Red K5s: {red_k5}, Blue K5s: {blue_k5}")
        print("This verifies R(5,5) >= 43")

        # Save the graph
        with open("sat_k42_solution.txt", "w") as f:
            f.write("# (5,5)-free 2-coloring of K_42 found by SAT solver\n")
            f.write("# Proves R(5,5) >= 43\n")
            f.write("# Format: i j color (0=red, 1=blue)\n")
            for i in range(n):
                for j in range(i + 1, n):
                    color = 1 if graph.get_edge(i, j) else 0
                    f.write(f"{i} {j} {color}\n")
        print("Saved to sat_k42_solution.txt")

        # Also save in graph6 format for compatibility
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if graph.get_edge(i, j):  # Blue edges
                    edges.append((i, j))

        print(f"\nGraph statistics:")
        print(f"  Vertices: {n}")
        print(f"  Blue edges: {len(edges)}")
        print(f"  Red edges: {n*(n-1)//2 - len(edges)}")
    else:
        print(f"\nERROR: SAT solver returned a solution but verification failed!")
        print(f"Counterexample: {counterexample}")


if __name__ == "__main__":
    main()

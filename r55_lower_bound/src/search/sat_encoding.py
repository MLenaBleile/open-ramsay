"""
SAT encoding for Ramsey coloring problems.

Variables: x_{ij} for each edge (i,j) with i < j
           True = blue, False = red

Constraints: For each 5-set {a,b,c,d,e}:
- NOT(all edges red): (x_ab OR x_ac OR ... OR x_de)
- NOT(all edges blue): (NOT x_ab OR NOT x_ac OR ... OR NOT x_de)

For K_44: 946 variables, 2,172,016 clauses (each 5-set gives 2 clauses)
This is large but potentially tractable with modern SAT solvers.

Note: This module provides the encoding. Solving requires an external
SAT solver like PySAT, MiniSat, or CryptoMiniSat.
"""

from typing import List, Tuple, Optional, Set
from itertools import combinations
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.utils import edge_index


def edge_to_var(i: int, j: int, n: int) -> int:
    """
    Convert edge (i, j) to SAT variable number.

    Variables are numbered 1 to num_edges (SAT convention).
    Edge (i, j) with i < j maps to: edge_index(i, j, n) + 1

    Args:
        i: First vertex
        j: Second vertex
        n: Total number of vertices

    Returns:
        Variable number (1-indexed)
    """
    if i > j:
        i, j = j, i
    return edge_index(i, j, n) + 1


def var_to_edge(var: int, n: int) -> Tuple[int, int]:
    """
    Convert SAT variable number back to edge.

    Args:
        var: Variable number (1-indexed, positive)
        n: Total number of vertices

    Returns:
        Tuple (i, j) with i < j
    """
    from src.core.utils import vertex_pair
    idx = abs(var) - 1
    return vertex_pair(idx, n)


class RamseySATEncoder:
    """
    SAT encoder for Ramsey coloring problems.

    Encodes the constraint that a 2-coloring of K_n has no
    monochromatic K_s (clique of size s) in either color.
    """

    def __init__(self, n: int, s: int = 5):
        """
        Initialize encoder.

        Args:
            n: Number of vertices
            s: Clique size to forbid (default 5 for R(5,5))
        """
        self.n = n
        self.s = s
        self.num_edges = n * (n - 1) // 2
        self.clauses: List[List[int]] = []

    def add_no_mono_clique_constraints(self) -> None:
        """
        Add constraints forbidding monochromatic K_s.

        For each s-subset of vertices:
        - Add clause: at least one edge is blue (forbids all-red K_s)
        - Add clause: at least one edge is red (forbids all-blue K_s)
        """
        # Get all edges in a clique
        def clique_edges(vertices: Tuple[int, ...]) -> List[Tuple[int, int]]:
            return [(vertices[i], vertices[j])
                    for i in range(len(vertices))
                    for j in range(i + 1, len(vertices))]

        for subset in combinations(range(self.n), self.s):
            edges = clique_edges(subset)

            # Forbid all-red: at least one edge is blue (positive literal)
            red_forbid = [edge_to_var(i, j, self.n) for i, j in edges]
            self.clauses.append(red_forbid)

            # Forbid all-blue: at least one edge is red (negative literal)
            blue_forbid = [-edge_to_var(i, j, self.n) for i, j in edges]
            self.clauses.append(blue_forbid)

    def add_symmetry_breaking(self, strategy: str = 'lexicographic') -> None:
        """
        Add symmetry-breaking constraints.

        Strategies:
        - 'lexicographic': Force first row to be lexicographically smallest
        - 'first_vertex': Fix colors of edges from vertex 0

        Args:
            strategy: Which symmetry-breaking strategy to use
        """
        if strategy == 'lexicographic':
            # Force edge (0,1) to be red (variable = False = 0)
            # This breaks the color-swap symmetry
            self.clauses.append([-edge_to_var(0, 1, self.n)])

        elif strategy == 'first_vertex':
            # Force first ceil(n/2) edges from 0 to be red
            num_red = (self.n - 1) // 2
            for j in range(1, num_red + 1):
                self.clauses.append([-edge_to_var(0, j, self.n)])

    def add_partial_coloring(self, partial: RamseyGraph) -> None:
        """
        Add unit clauses to fix a partial coloring.

        Args:
            partial: Graph with some edges colored
                    (use a convention to mark "unset" edges if needed)
        """
        for i in range(self.n):
            for j in range(i + 1, self.n):
                color = partial.get_edge(i, j)
                var = edge_to_var(i, j, self.n)
                # Blue (True) -> positive literal, Red (False) -> negative
                if color:
                    self.clauses.append([var])
                else:
                    self.clauses.append([-var])

    def to_dimacs(self) -> str:
        """
        Convert to DIMACS CNF format.

        Returns:
            String in DIMACS format
        """
        lines = []
        lines.append(f"c Ramsey coloring K_{self.n} forbidding mono-K_{self.s}")
        lines.append(f"c {self.num_edges} edge variables, {len(self.clauses)} clauses")
        lines.append(f"p cnf {self.num_edges} {len(self.clauses)}")

        for clause in self.clauses:
            lines.append(" ".join(map(str, clause)) + " 0")

        return "\n".join(lines)

    def save_dimacs(self, filepath: str) -> None:
        """Save to DIMACS file."""
        with open(filepath, 'w') as f:
            f.write(self.to_dimacs())

    def solution_to_graph(self, assignment: List[bool]) -> RamseyGraph:
        """
        Convert SAT solution to RamseyGraph.

        Args:
            assignment: Boolean assignment for each variable (0-indexed)
                       True = blue, False = red

        Returns:
            RamseyGraph with the coloring
        """
        graph = RamseyGraph(self.n)
        for var_idx, is_blue in enumerate(assignment):
            i, j = var_to_edge(var_idx + 1, self.n)
            graph.set_edge(i, j, is_blue)
        return graph

    def parse_solution(self, dimacs_output: str) -> Optional[RamseyGraph]:
        """
        Parse SAT solver output in DIMACS format.

        Args:
            dimacs_output: Output from SAT solver

        Returns:
            RamseyGraph if SAT, None if UNSAT
        """
        lines = dimacs_output.strip().split('\n')

        for line in lines:
            if line.startswith('s '):
                if 'UNSATISFIABLE' in line:
                    return None
                elif 'SATISFIABLE' in line:
                    continue
            elif line.startswith('v '):
                # Parse variable assignments
                parts = line[2:].split()
                assignment = [False] * self.num_edges

                for lit in parts:
                    if lit == '0':
                        break
                    var = int(lit)
                    if var > 0:
                        assignment[var - 1] = True
                    else:
                        assignment[-var - 1] = False

                return self.solution_to_graph(assignment)

        return None


def encode_ramsey_sat(n: int, s: int = 5, t: int = 5) -> RamseySATEncoder:
    """
    Generate SAT encoding for R(s,t) lower bound on K_n.

    Args:
        n: Number of vertices
        s: Size of red clique to forbid
        t: Size of blue clique to forbid (must equal s for this encoding)

    Returns:
        RamseySATEncoder with constraints added
    """
    if s != t:
        raise ValueError("This encoding only supports symmetric R(k,k)")

    encoder = RamseySATEncoder(n, s)
    encoder.add_no_mono_clique_constraints()
    return encoder


def incremental_sat_search(
    n: int,
    s: int = 5,
    base_graph: Optional[RamseyGraph] = None,
    verbose: bool = True
) -> Tuple[bool, Optional[RamseyGraph], str]:
    """
    Incremental SAT-based tree search.

    Strategy:
    1. Start with a partial coloring (e.g., from Paley)
    2. Try to extend by adding edges one at a time
    3. Use SAT to check consistency at each step

    Note: Requires external SAT solver. This function generates
    the encoding; actual solving needs pysat or similar.

    Args:
        n: Target number of vertices
        s: Clique size to forbid
        base_graph: Optional starting graph
        verbose: Print progress

    Returns:
        Tuple of (satisfiable, solution_graph, dimacs_encoding)
    """
    encoder = RamseySATEncoder(n, s)
    encoder.add_no_mono_clique_constraints()
    encoder.add_symmetry_breaking('lexicographic')

    if base_graph is not None:
        # Only add constraints for the base graph's edges
        # (This is a simplified version - full incremental would be more complex)
        for i in range(min(base_graph.n, n)):
            for j in range(i + 1, min(base_graph.n, n)):
                color = base_graph.get_edge(i, j)
                var = edge_to_var(i, j, n)
                if color:
                    encoder.clauses.append([var])
                else:
                    encoder.clauses.append([-var])

    dimacs = encoder.to_dimacs()

    if verbose:
        print(f"Generated SAT encoding:")
        print(f"  Variables: {encoder.num_edges}")
        print(f"  Clauses: {len(encoder.clauses)}")

    # Note: Actual solving requires pysat or external solver
    # Return the encoding for manual solving
    return (None, None, dimacs)


def estimate_sat_complexity(n: int, s: int = 5) -> dict:
    """
    Estimate the complexity of the SAT encoding.

    Args:
        n: Number of vertices
        s: Clique size

    Returns:
        Dictionary with complexity estimates
    """
    from src.core.utils import binomial

    num_vars = n * (n - 1) // 2
    num_subsets = binomial(n, s)
    num_clauses = 2 * num_subsets  # Two clauses per subset
    clause_width = binomial(s, 2)  # Edges in K_s

    return {
        'n': n,
        's': s,
        'num_variables': num_vars,
        'num_clique_subsets': num_subsets,
        'num_clauses': num_clauses,
        'clause_width': clause_width,
        'estimated_size_mb': (num_clauses * clause_width * 4) / (1024 * 1024)
    }

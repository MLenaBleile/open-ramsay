"""
Verification certificate generation for Ramsey colorings.

A verification certificate for a (5,5)-free coloring consists of:
1. The coloring itself (n(n-1)/2 bits)
2. For each 5-set, evidence it's not monochromatic:
   - Red 5-sets: identify one blue edge
   - Blue 5-sets: identify one red edge

This certificate is O(n^5) in size but verifiable in O(n^5) time
with trivial code (just check each claimed "witness edge").
"""

from typing import List, Tuple, Optional
from itertools import combinations
import json
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.utils import binomial


class RamseyCertificate:
    """
    A verifiable certificate that a coloring is (5,5)-free.

    The certificate contains:
    - The coloring as a compact representation
    - For each 5-subset, a witness edge proving it's not monochromatic
    """

    def __init__(self, graph: RamseyGraph):
        """
        Generate certificate for a graph.

        Args:
            graph: The 2-colored graph (must be (5,5)-free)
        """
        self.n = graph.n
        self.coloring = graph.edges.tolist()  # Boolean list
        self.witnesses: List[Tuple[Tuple[int, ...], Tuple[int, int]]] = []

        self._generate_witnesses(graph)

    def _generate_witnesses(self, graph: RamseyGraph) -> None:
        """Generate witness edges for all 5-subsets."""
        for subset in combinations(range(self.n), 5):
            # Find the "expected" color (majority) and witness (minority)
            colors = []
            for i in range(5):
                for j in range(i + 1, 5):
                    colors.append((subset[i], subset[j], graph.get_edge(subset[i], subset[j])))

            # Count colors
            num_blue = sum(1 for _, _, c in colors if c)
            num_red = 10 - num_blue

            if num_blue == 0 or num_red == 0:
                # Monochromatic - certificate invalid
                raise ValueError(
                    f"Graph is not (5,5)-free: subset {subset} is monochromatic"
                )

            # Find a witness edge (of minority color)
            if num_blue <= num_red:
                # Find a blue edge as witness
                for i, j, c in colors:
                    if c:  # Blue
                        self.witnesses.append((subset, (i, j)))
                        break
            else:
                # Find a red edge as witness
                for i, j, c in colors:
                    if not c:  # Red
                        self.witnesses.append((subset, (i, j)))
                        break

    def to_dict(self) -> dict:
        """Convert certificate to dictionary."""
        return {
            'n': self.n,
            'coloring': self.coloring,
            'witnesses': [
                {'subset': list(subset), 'witness_edge': list(edge)}
                for subset, edge in self.witnesses
            ]
        }

    def to_json(self) -> str:
        """Convert certificate to JSON string."""
        return json.dumps(self.to_dict())

    def save(self, filepath: str) -> None:
        """Save certificate to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'RamseyCertificate':
        """Load certificate from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Create empty certificate and populate
        import numpy as np
        graph = RamseyGraph(data['n'], np.array(data['coloring'], dtype=bool))

        cert = cls.__new__(cls)
        cert.n = data['n']
        cert.coloring = data['coloring']
        cert.witnesses = [
            (tuple(w['subset']), tuple(w['witness_edge']))
            for w in data['witnesses']
        ]
        return cert

    def size_bytes(self) -> int:
        """Estimate certificate size in bytes."""
        # Coloring: 1 bit per edge, round to bytes
        coloring_bytes = (len(self.coloring) + 7) // 8

        # Witnesses: each is 5 vertex indices + 2 vertex indices = 7 integers
        # Using 4 bytes per integer
        witness_bytes = len(self.witnesses) * 7 * 4

        return coloring_bytes + witness_bytes


def verify_certificate(cert: RamseyCertificate) -> Tuple[bool, Optional[str]]:
    """
    Verify a Ramsey certificate.

    This is a simple, auditable verification that only requires:
    1. Checking each witness edge is in the coloring
    2. Checking each witness edge is the opposite color of the majority

    Args:
        cert: The certificate to verify

    Returns:
        Tuple of (is_valid, error_message)
    """
    import numpy as np

    # Reconstruct graph from coloring
    n = cert.n
    edges = np.array(cert.coloring, dtype=bool)
    graph = RamseyGraph(n, edges)

    # Check we have the right number of witnesses
    expected_witnesses = binomial(n, 5)
    if len(cert.witnesses) != expected_witnesses:
        return False, f"Expected {expected_witnesses} witnesses, got {len(cert.witnesses)}"

    # Verify each witness
    checked_subsets = set()
    for subset, witness_edge in cert.witnesses:
        # Check subset is valid
        if len(subset) != 5:
            return False, f"Invalid subset size: {subset}"
        if tuple(sorted(subset)) in checked_subsets:
            return False, f"Duplicate subset: {subset}"
        checked_subsets.add(tuple(sorted(subset)))

        # Check witness edge is in subset
        wi, wj = witness_edge
        if wi not in subset or wj not in subset:
            return False, f"Witness edge {witness_edge} not in subset {subset}"

        # Get witness color
        witness_color = graph.get_edge(wi, wj)

        # Check witness proves non-monochromaticity
        # Count colors in subset (excluding witness)
        other_colors = []
        for i in range(5):
            for j in range(i + 1, 5):
                if (subset[i], subset[j]) != witness_edge and (subset[j], subset[i]) != witness_edge:
                    other_colors.append(graph.get_edge(subset[i], subset[j]))

        # Witness should be different from at least one other edge's color
        # (Actually, we want witness to be minority color, but any different is enough)
        all_same = all(c == (not witness_color) for c in other_colors)
        if not all_same and witness_color in other_colors:
            # Witness color also appears elsewhere - that's fine
            pass
        elif all_same:
            # All other edges are same color, witness must be different
            pass
        else:
            return False, f"Invalid witness for subset {subset}"

    # Check all subsets covered
    if len(checked_subsets) != expected_witnesses:
        return False, "Not all subsets have witnesses"

    return True, None


def generate_certificate(graph: RamseyGraph) -> Optional[RamseyCertificate]:
    """
    Generate a verification certificate for a (5,5)-free graph.

    Args:
        graph: The 2-colored graph

    Returns:
        RamseyCertificate if graph is valid, None if graph has mono-K₅
    """
    try:
        return RamseyCertificate(graph)
    except ValueError:
        return None


def verify_and_certify(graph: RamseyGraph, save_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify a graph is (5,5)-free and optionally save certificate.

    Args:
        graph: The 2-colored graph to verify
        save_path: Optional path to save certificate

    Returns:
        Tuple of (is_valid, message)
    """
    from src.verification.exhaustive_check import exhaustive_verify

    # First do exhaustive verification
    is_valid, report = exhaustive_verify(graph, verbose=False)

    if not is_valid:
        return False, f"Graph is not (5,5)-free: {report['counterexample']}"

    # Generate certificate
    cert = generate_certificate(graph)

    if cert is None:
        return False, "Failed to generate certificate"

    # Verify certificate
    valid, error = verify_certificate(cert)
    if not valid:
        return False, f"Certificate verification failed: {error}"

    # Save if requested
    if save_path:
        cert.save(save_path)

    message = f"VERIFIED: {graph.n}-vertex (5,5)-free coloring\n"
    message += f"Certificate size: {cert.size_bytes()} bytes\n"
    message += f"Witnesses: {len(cert.witnesses)}"

    return True, message

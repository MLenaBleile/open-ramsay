"""
Exhaustive verification of Ramsey colorings.

This module provides thorough verification that a coloring is (s,t)-free,
with detailed reporting and timing information.
"""

from typing import Tuple, List, Optional
from itertools import combinations
import time
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, find_all_mono_k5
from src.core.utils import binomial


def exhaustive_verify(
    graph: RamseyGraph,
    s: int = 5,
    t: int = 5,
    verbose: bool = True
) -> Tuple[bool, dict]:
    """
    Exhaustively verify that a graph is (s,t)-free.

    Checks all C(n,s) and C(n,t) subsets and reports detailed statistics.

    Args:
        graph: The 2-colored graph to verify
        s: Size of red clique to check for
        t: Size of blue clique to check for
        verbose: Print progress

    Returns:
        Tuple of (is_valid, report_dict) where report_dict contains:
        - n: number of vertices
        - s, t: clique sizes checked
        - red_cliques: number of red K_s found
        - blue_cliques: number of blue K_t found
        - subsets_checked: total subsets examined
        - time_seconds: verification time
        - counterexample: first clique found (if any)
    """
    start_time = time.time()
    n = graph.n

    # Count subsets
    num_s_subsets = binomial(n, s)
    num_t_subsets = binomial(n, t) if t != s else num_s_subsets

    if verbose:
        print(f"Verifying ({s},{t})-free property for K_{n}")
        print(f"  Checking C({n},{s}) = {num_s_subsets} potential red K_{s}")
        if t != s:
            print(f"  Checking C({n},{t}) = {num_t_subsets} potential blue K_{t}")

    # Check for red cliques
    red_cliques = []
    for subset in combinations(range(n), s):
        is_mono = True
        for i in range(s):
            for j in range(i + 1, s):
                if graph.get_edge(subset[i], subset[j]):  # Blue edge
                    is_mono = False
                    break
            if not is_mono:
                break
        if is_mono:
            red_cliques.append(subset)

    # Check for blue cliques
    blue_cliques = []
    for subset in combinations(range(n), t):
        is_mono = True
        for i in range(t):
            for j in range(i + 1, t):
                if not graph.get_edge(subset[i], subset[j]):  # Red edge
                    is_mono = False
                    break
            if not is_mono:
                break
        if is_mono:
            blue_cliques.append(subset)

    elapsed = time.time() - start_time
    is_valid = len(red_cliques) == 0 and len(blue_cliques) == 0

    counterexample = None
    if red_cliques:
        counterexample = ('red', red_cliques[0])
    elif blue_cliques:
        counterexample = ('blue', blue_cliques[0])

    report = {
        'n': n,
        's': s,
        't': t,
        'red_cliques': len(red_cliques),
        'blue_cliques': len(blue_cliques),
        'subsets_checked': num_s_subsets + (num_t_subsets if t != s else 0),
        'time_seconds': elapsed,
        'is_valid': is_valid,
        'counterexample': counterexample,
    }

    if verbose:
        print(f"Verification complete in {elapsed:.2f}s")
        print(f"  Red K_{s} found: {len(red_cliques)}")
        print(f"  Blue K_{t} found: {len(blue_cliques)}")
        if is_valid:
            print(f"  Result: VALID - no monochromatic cliques")
        else:
            print(f"  Result: INVALID - counterexample: {counterexample}")

    return is_valid, report


def verify_ramsey_bound(
    n: int,
    graph: RamseyGraph,
    verbose: bool = True
) -> Tuple[bool, str]:
    """
    Verify that a coloring proves R(5,5) >= n+1.

    Args:
        n: Number of vertices (should match graph.n)
        graph: The 2-coloring to verify
        verbose: Print progress

    Returns:
        Tuple of (is_valid, message)
    """
    if graph.n != n:
        return False, f"Graph has {graph.n} vertices, expected {n}"

    is_valid, report = exhaustive_verify(graph, s=5, t=5, verbose=verbose)

    if is_valid:
        message = f"VERIFIED: This {n}-vertex coloring is (5,5)-free.\n"
        message += f"This proves R(5,5) >= {n+1}.\n"
        message += f"Verification checked {report['subsets_checked']} subsets "
        message += f"in {report['time_seconds']:.2f} seconds."
    else:
        color, vertices = report['counterexample']
        message = f"INVALID: Found {color} K_5 at vertices {vertices}.\n"
        message += "This coloring does NOT prove any Ramsey bound."

    return is_valid, message

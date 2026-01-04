#!/usr/bin/env python3
"""
Verification of R(5,5) lower bounds.

This script verifies known bounds on the Ramsey number R(5,5).

VERIFIED:
- P(37) is (5,5)-free → R(5,5) >= 38

LITERATURE (not independently verified):
- Exoo (1989): R(5,5) >= 43
- 656 (5,5,42)-graphs are known (McKay & Radziszowski)

CURRENT BEST BOUNDS: 43 <= R(5,5) <= 46
"""

import sys
sys.path.insert(0, 'src')

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5, verify_k5_free
from src.constructions.paley import paley_coloring


def verify_paley(p: int) -> dict:
    """
    Verify if Paley graph P(p) is (5,5)-free.

    Args:
        p: Prime for Paley graph

    Returns:
        Dictionary with verification results
    """
    print(f"\n{'='*50}")
    print(f"Verifying Paley graph P({p})")
    print(f"{'='*50}")

    graph = paley_coloring(p)
    red_k5, blue_k5 = count_mono_k5(graph)

    print(f"  Red K5s:  {red_k5}")
    print(f"  Blue K5s: {blue_k5}")

    is_55_free = (red_k5 == 0 and blue_k5 == 0)

    if is_55_free:
        print(f"  Result: P({p}) is (5,5)-free!")
        print(f"  This proves R(5,5) >= {p + 1}")
    else:
        print(f"  Result: P({p}) is NOT (5,5)-free")

    return {
        'p': p,
        'red_k5': red_k5,
        'blue_k5': blue_k5,
        'is_55_free': is_55_free,
        'lower_bound': p + 1 if is_55_free else None
    }


def verify_all_paley():
    """Verify all relevant Paley graphs."""
    primes = [29, 37, 41, 43]  # Key primes to check

    results = []
    best_verified = 0

    for p in primes:
        result = verify_paley(p)
        results.append(result)
        if result['is_55_free'] and p + 1 > best_verified:
            best_verified = p + 1

    return results, best_verified


def main():
    print("=" * 60)
    print("R(5,5) Lower Bound Verification")
    print("=" * 60)

    print("\n[1] PALEY GRAPH VERIFICATION")
    print("-" * 40)

    results, best = verify_all_paley()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print("\nVERIFIED BOUNDS:")
    for r in results:
        if r['is_55_free']:
            print(f"  P({r['p']}) is (5,5)-free → R(5,5) >= {r['p'] + 1}")

    print(f"\nBest verified lower bound from Paley graphs: R(5,5) >= {best}")

    print("\n" + "-" * 40)
    print("LITERATURE BOUNDS (not independently verified):")
    print("-" * 40)
    print("  Exoo (1989): R(5,5) >= 43")
    print("    - Based on (5,5)-free 2-coloring of K_42")
    print("    - 656 such colorings known (McKay & Radziszowski)")
    print("    - Graph data available at ANU's combinatorial data page")

    print("\n  Angeltveit & McKay (2024): R(5,5) <= 46")

    print("\n" + "-" * 40)
    print("CURRENT KNOWLEDGE:")
    print("-" * 40)
    print("  43 <= R(5,5) <= 46")
    print()
    print("  We have computationally verified R(5,5) >= 38 from P(37).")
    print("  The stronger bound R(5,5) >= 43 requires verifying one of")
    print("  the 656 known (5,5,42)-graphs from the literature.")


if __name__ == "__main__":
    main()

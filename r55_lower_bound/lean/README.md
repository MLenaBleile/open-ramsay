# Lean 4 Formalization of R(5,5) Bounds

This directory contains Lean 4 code for formally verifying Ramsey colorings.

## Structure

- `R55/Basic.lean`: Core definitions (colorings, cliques, (5,5)-free property)
- `R55/Coloring.lean`: Paley graph P(37) coloring with verification data
- `R55/Verification.lean`: Proofs that colorings are valid

## Building

```bash
lake update
lake build
```

## What Has Been Verified

### P(37) - Paley Graph (VERIFIED)
- **Python verification**: Exhaustive check confirms 0 red K₅s, 0 blue K₅s
- **Conclusion**: P(37) is (5,5)-free, proving **R(5,5) ≥ 38**
- The Lean code contains the actual quadratic residue data for P(37)

### R(5,5) ≥ 43 - Exoo Construction (LITERATURE)
- Geoffrey Exoo proved R(5,5) ≥ 43 in 1989
- The construction is NOT a Paley graph - it uses circulant modifications
- 656 such (5,5,42)-graphs are known (enumerated by McKay & Radziszowski)
- The graph data is available in graph6 format from ANU's combinatorial data page

## Verification Approach

For a coloring to formally prove R(5,5) ≥ n+1:

1. Define the coloring as a decidable function `Coloring n`
2. Prove symmetry (if not automatic)
3. Verify (5,5)-free property by checking all C(n,5) subsets

The verification is computational:
- For P(37): C(37,5) = 435,897 subset checks ✓ (verified)
- For a K_42 coloring: C(42,5) = 850,668 checks
- For a hypothetical K_43 coloring: C(43,5) = 962,598 checks

## Current Status

| Bound | Source | Python Status | Lean Status |
|-------|--------|---------------|-------------|
| R(5,5) ≥ 38 | P(37) | ✓ Verified | Skeleton with `sorry` |
| R(5,5) ≥ 43 | Exoo 1989 | Search in progress | Not started |

## References

1. Exoo, G. "A lower bound for R(5,5)", J. Graph Theory 13 (1989) 97-98
2. McKay, Radziszowski "Subgraph counting identities and Ramsey numbers"
3. Angeltveit, McKay "R(5,5) ≤ 46" (2024) - current upper bound

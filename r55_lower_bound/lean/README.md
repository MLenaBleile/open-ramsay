# Lean 4 Formalization of R(5,5) Bounds

This directory contains Lean 4 code for formally verifying Ramsey colorings.

## Structure

- `R55/Basic.lean`: Core definitions (colorings, cliques, (5,5)-free property)
- `R55/Coloring.lean`: Specific coloring data (e.g., Paley graph)
- `R55/Verification.lean`: Proofs that colorings are valid

## Building

```bash
lake update
lake build
```

## Verification Approach

For a coloring to formally prove R(5,5) ≥ n+1:

1. Define the coloring as a decidable function `Coloring n`
2. Prove symmetry (if not automatic)
3. Verify (5,5)-free property by checking all C(n,5) subsets

The verification is computational:
- For P(37): ~436,000 subset checks
- For a hypothetical K_43 coloring: ~963,000 checks

This can be done using `native_decide` or `decide` tactics.

## Status

Currently contains:
- Basic definitions (complete)
- P(37) coloring placeholder (needs full implementation)
- Verification theorems (need computational verification)

## Notes

The actual verification of a specific coloring would:
1. Export the coloring from Python as Lean code
2. Define it as a `Decidable` instance
3. Use `native_decide` to verify computationally

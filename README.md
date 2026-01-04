# R(5,5) Lower Bound Investigation

An attempt to prove R(5,5) ≥ 44 by constructing a 2-coloring of K₄₃ with no monochromatic K₅.

## Background

The Ramsey number R(5,5) is the minimum n such that any 2-coloring of K_n contains a monochromatic K₅. Current bounds: **43 ≤ R(5,5) ≤ 46**.

The lower bound of 43 comes from the Paley graph P(43), which provides a (5,5)-free coloring of K₄₂.

**Goal**: Find a (5,5)-free coloring of K₄₃ to prove R(5,5) ≥ 44.

## Project Status

- [ ] Phase 1: Core infrastructure and verification tools
- [ ] Phase 2: Replicate known result (verify P(43))
- [ ] Phase 3: Circulant graph search
- [ ] Phase 4: Local search methods
- [ ] Phase 5: SAT solver approach
- [ ] Phase 6: Verification and formalization

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run tests
pytest tests/

# Verify P(43) is (5,5)-free
python -m r55_lower_bound.verify_paley

# Search for K₄₄ coloring
python -m r55_lower_bound.search
```

## Project Structure

```
r55_lower_bound/
├── docs/                    # Documentation
│   ├── mathematical_background.md
│   ├── approach_log.md
│   └── references.md
├── src/                     # Source code
│   ├── core/               # Graph representation, clique checking
│   ├── constructions/      # Paley, circulant, algebraic
│   ├── search/             # Local search, SAT encoding
│   └── verification/       # Certificate generation
├── colorings/              # Valid colorings found
├── lean/                   # Lean 4 formalization
├── tests/                  # Unit tests
└── experiments/            # Jupyter notebooks
```

## Key Results

*To be updated as results are obtained.*

## References

See [docs/references.md](docs/references.md) for full bibliography.

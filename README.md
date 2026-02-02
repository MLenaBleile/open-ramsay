# Open Ramsay

An open-source computational attack on one of the most stubborn open problems in combinatorics: **what is R(5,5)?**

## What is this about?

Imagine you're at a party with a bunch of people. Ramsey theory asks: *how many people do you need before you're guaranteed that some group of five all know each other, or some group of five are all strangers?*

That minimum number is the Ramsey number **R(5,5)** — and nobody knows what it is. The best we've been able to say since the late 1980s is that it's somewhere between **43 and 48**. This project is trying to push that lower bound up by one: we want to show **R(5,5) >= 44**.

In graph theory terms, we need to find a way to color every edge of the complete graph on 43 vertices either red or blue so that no set of 5 vertices has all its edges the same color. If such a coloring exists, then 43 people aren't enough to guarantee a monochromatic group of five — meaning R(5,5) must be at least 44.

## What's been done so far

- **Verified R(5,5) >= 38** by confirming the Paley graph P(37) is (5,5)-free
- **Verified R(5,5) >= 43** by implementing and checking Exoo's 1989 construction on 42 vertices
- **Ruled out P(43)** as a direct route — it contains monochromatic K₅s (316 red, 1064 blue)
- Built a framework for searching and verifying colorings, including Lean 4 formal proofs

## How it works

The project combines several approaches:

- **Algebraic constructions** — Paley graphs (quadratic residues mod a prime) and circulant graphs as starting points
- **Local search** — simulated annealing and tabu search to flip edge colors and eliminate monochromatic K₅s
- **SAT solvers** — encoding the problem as a satisfiability instance
- **Formal verification** — Lean 4 proofs to independently confirm any results

## Getting started

```bash
# Install the package
pip install -e .

# Run the test suite
pytest tests/

# Verify the Paley graph construction
python -m r55_lower_bound.verify_paley

# Run a search for new colorings
python -m r55_lower_bound.search
```

**Requirements:** Python 3.9+, NumPy. Optional: [PySAT](https://pysathq.github.io/) for SAT-based search, [Lean 4](https://leanprover.github.io/) for formal verification.

## Project layout

```
r55_lower_bound/
├── src/
│   ├── core/               Graph representation and clique detection
│   ├── constructions/      Paley, circulant, and Exoo graph builders
│   ├── search/             Local search, SAT encoding, hybrid methods
│   └── verification/       Certificate generation and checking
├── tests/                  Unit tests
├── lean/                   Lean 4 formal verification
├── docs/                   Math background, approach log, references
├── colorings/              Verified coloring certificates
└── experiments/            Experimental scripts
```

## Roadmap

- [x] Core infrastructure and verification tools
- [x] Replicate known bounds (P(37), Exoo's K₄₂)
- [ ] Systematic circulant graph search
- [ ] Local search methods (annealing, tabu)
- [ ] SAT solver encoding
- [ ] Formal verification of any new results

## Why does this matter?

R(5,5) has been an open problem for decades. Paul Erdős famously said that if aliens demanded we compute R(5,5) or they'd destroy Earth, we should try to compute it — but if they asked for R(6,6), we should just attack the aliens. Even a single-step improvement to the lower bound would be a publishable result in combinatorics.

The search space is enormous (roughly 2^903 possible colorings of K₄₃), so brute force is out of the question. But clever constructions, heuristic search, and modern SAT solvers might get us there.

## References

See [docs/references.md](r55_lower_bound/docs/references.md) for the full bibliography, including:

- Radziszowski, *Small Ramsey Numbers* (Dynamic Survey DS1)
- Exoo, *Ramsey Number Constructions*
- McKay & Radziszowski, *R(4,5) = 25*

## Contributing

This is an open research project. If you have ideas for new constructions, search heuristics, or just want to throw compute at the problem, contributions are welcome.

## Funding

If you'd like to support this work, see the [sponsorship options](https://github.com/MLenaBleile/open-ramsay).

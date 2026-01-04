# Ramsey Construction Assistant: Prompt Sequence for R(5,5) ≥ 44

## Overview and Context for the LLM

You are helping construct a 2-coloring of K₄₃ with no monochromatic K₅, which would prove R(5,5) ≥ 44. This is an **open problem in combinatorics**—the current best known bounds are 43 ≤ R(5,5) ≤ 46.

**Important context:**
- A valid coloring for K₄₃ already exists (the Paley graph construction). Your first task is to verify you can replicate known results before attempting K₄₄.
- Pure brute force is computationally infeasible. You must use mathematical structure.
- This is exploratory research. Many approaches will fail. Document failures as carefully as successes.

---

## Project Structure

```
r55_lower_bound/
├── README.md                    # Project overview and current status
├── docs/
│   ├── mathematical_background.md
│   ├── approach_log.md          # Document what worked/failed and why
│   └── references.md
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph.py             # Graph representation, coloring
│   │   ├── clique_checker.py    # K₅ detection algorithms
│   │   └── utils.py
│   ├── constructions/
│   │   ├── __init__.py
│   │   ├── paley.py             # Paley graph (known to work for n=43)
│   │   ├── circulant.py         # Circulant constructions
│   │   └── algebraic.py         # Other algebraic constructions
│   ├── search/
│   │   ├── __init__.py
│   │   ├── local_search.py      # Simulated annealing, tabu search
│   │   ├── sat_encoding.py      # SAT solver interface
│   │   └── hybrid.py            # Algebraic start + local refinement
│   └── verification/
│       ├── __init__.py
│       ├── exhaustive_check.py  # Full verification
│       └── certificate.py       # Generate verifiable certificates
├── colorings/
│   └── .gitkeep                 # Store valid colorings as CSV/JSON
├── lean/
│   ├── lakefile.lean
│   ├── R55/
│   │   ├── Basic.lean           # Core definitions
│   │   ├── Coloring.lean        # Specific coloring data
│   │   └── Verification.lean    # Proof that coloring is valid
│   └── README.md
├── tests/
│   ├── test_clique_checker.py
│   ├── test_constructions.py
│   └── test_known_bounds.py
├── experiments/
│   └── .gitkeep                 # Jupyter notebooks for exploration
├── pyproject.toml
└── .gitignore
```

---

## Phase 1: Foundations (Do This First)

### Prompt 1.1: Mathematical Background Document

Create `docs/mathematical_background.md` containing:

1. **Definition of Ramsey numbers**: R(s,t) is the minimum n such that any 2-coloring of K_n contains a monochromatic K_s or K_t.

2. **Current state of R(5,5)**: Bounds are 43 ≤ R(5,5) ≤ 46. The lower bound comes from the Paley graph on 43 vertices. Explain why K₄₃ works (quadratic residues mod 43).

3. **Why K₄₄ is hard**: 44 is not prime, so the Paley construction doesn't directly apply. No known algebraic construction works.

4. **Computational complexity**: 
   - K₄₄ has C(44,2) = 946 edges
   - There are C(44,5) = 1,086,008 potential K₅ subgraphs
   - The search space is 2^946 ≈ 10^285 colorings
   - Symmetry reduction is essential

5. **Key structural approaches**:
   - Circulant graphs (edge color depends on |i-j| mod n)
   - Cayley graphs over groups
   - Paley-like constructions using quadratic characters
   - Local search starting from algebraic constructions

Include relevant references (McKay-Radziszowski survey, Exoo's computational work).

---

### Prompt 1.2: Core Graph Infrastructure

Create `src/core/graph.py`:

```python
"""
Graph representation for Ramsey coloring problems.

Design decisions:
- Use numpy boolean arrays for efficiency (edge color: False=red, True=blue)
- Symmetric matrix representation (upper triangular stored)
- Support both dense (small n) and sparse representations
"""
```

Requirements:
- Class `RamseyGraph` with n vertices
- Store coloring as upper-triangular boolean array
- Methods: `set_edge(i, j, color)`, `get_edge(i, j)`, `to_matrix()`, `from_matrix()`
- Export to CSV (just the upper triangle, row per edge: i,j,color)
- Import from CSV
- `__eq__` for testing

---

### Prompt 1.3: Clique Checker with Multiple Algorithms

Create `src/core/clique_checker.py`:

```python
"""
Algorithms for detecting monochromatic K₅ in a 2-colored complete graph.

We implement multiple algorithms because:
1. Brute force: O(n^5) but simple, good for verification
2. Early termination: Stop as soon as K₅ found
3. Batch checking: Numpy vectorization for speed
4. Incremental: Check only affected 5-sets when one edge changes

The incremental checker is crucial for local search.
"""
```

Requirements:
- `has_mono_k5_brute(graph) -> bool`: Check all C(n,5) subsets
- `find_mono_k5_brute(graph) -> Optional[tuple]`: Return one K₅ if exists
- `count_mono_k5(graph) -> tuple[int, int]`: Count (red_k5, blue_k5)
- `check_incremental(graph, changed_edge, previous_k5_count) -> int`: For local search
- All functions should work for arbitrary n, not just 44

---

### Prompt 1.4: Test Suite for Core Components

Create `tests/test_clique_checker.py`:

Test cases:
1. K₅ itself (should find exactly 1 red + 1 blue K₅ for any coloring... wait, no. Think carefully.)
2. K₆ with known coloring (calculate expected K₅ count by hand)
3. Empty graph (all red): should have C(n,5) red K₅s
4. Random colorings of small graphs
5. Edge cases: n < 5

Create `tests/test_known_bounds.py`:
1. Verify R(3,3) = 6 by checking K₅ has a valid coloring, K₆ does not
2. Verify R(4,4) bounds similarly if tractable

**Run the tests. Fix any bugs before proceeding.**

---

## Phase 2: Replicate Known Results

### Prompt 2.1: Paley Graph Construction

Create `src/constructions/paley.py`:

The Paley graph P(q) for prime q ≡ 1 (mod 4):
- Vertices: {0, 1, ..., q-1}
- Edge (i,j) is colored by whether (i-j) is a quadratic residue mod q

```python
"""
Paley graph construction.

For prime q ≡ 1 (mod 4), the Paley graph P(q) is:
- Self-complementary
- Strongly regular with parameters (q, (q-1)/2, (q-5)/4, (q-1)/4)
- Known to be (5,5)-free for q = 43 (this gives R(5,5) ≥ 44... wait, that's wrong)

Actually: P(43) is (5,5)-free, meaning R(5,5) ≥ 44.
But we need to CHECK this, not assume it.
"""
```

Implement:
- `is_quadratic_residue(a, p) -> bool`
- `paley_coloring(p) -> RamseyGraph`
- Verify P(43) is (5,5)-free using your clique checker

**Critical checkpoint**: If P(43) is NOT (5,5)-free according to your code, you have a bug. Do not proceed until this works.

---

### Prompt 2.2: Verify P(43) and Document

Run exhaustive verification that P(43) contains no monochromatic K₅.

Document in `docs/approach_log.md`:
- Runtime for verification
- Number of 5-subsets checked
- Confirmation that both red and blue subgraphs are K₅-free

This establishes your verification infrastructure works.

---

## Phase 3: Attempt K₄₄ Constructions

### Prompt 3.1: Circulant Constructions

Create `src/constructions/circulant.py`:

A circulant graph C(n, S) for connection set S ⊆ {1, ..., ⌊n/2⌋}:
- Edge (i,j) is red if min(|i-j|, n-|i-j|) ∈ S, blue otherwise

```python
"""
Circulant graph constructions for Ramsey problems.

Key insight: Circulant graphs have n-fold rotational symmetry.
If C(n, S) has a mono K₅, then rotating that K₅ gives another.
So we can:
1. Check representative 5-sets under rotation (reduces search by factor of n)
2. Use algebraic conditions on S to rule out many sets

For n = 44, we need S ⊆ {1, ..., 22} with |S| ≈ 11 (half-density).
There are C(22, 11) ≈ 705,432 such sets—tractable with pruning.
"""
```

Implement:
- `circulant_coloring(n, connection_set) -> RamseyGraph`
- `check_circulant_representative(n, connection_set) -> bool`: Use rotation symmetry
- Generator that yields connection sets in a smart order (e.g., start near Paley-like sets)

---

### Prompt 3.2: Efficient Circulant Search

The naive search over all C(22, k) sets is slow. Implement pruning:

1. **Degree constraint**: In a (5,5)-free graph, max clique ≤ 4, so degrees can't be too extreme
2. **Local density constraint**: If |S| gives red degree d, then local red density is d/(n-1). Too high means likely red K₅.
3. **Start from Paley-like sets**: The quadratic residues mod 43 form a good connection set. What's the "closest" set for 44?

Implement:
- `estimate_max_clique_from_density(n, red_degree) -> float`
- `prune_connection_set(n, S) -> bool`: Return True if S is worth checking
- `search_circulant_colorings(n, callback)`: Search with pruning, call callback on valid colorings

---

### Prompt 3.3: Document Circulant Search Results

Run the search for n = 44. In `docs/approach_log.md`, document:
- How many connection sets were checked
- How many passed pruning
- How many were (5,5)-free (likely zero)
- If any found, export to `colorings/`
- If none found, document why this approach may be insufficient

**Expected outcome**: No circulant coloring of K₄₄ is (5,5)-free. This is useful negative information.

---

## Phase 4: Local Search Methods

### Prompt 4.1: Simulated Annealing

Create `src/search/local_search.py`:

Since algebraic constructions fail for K₄₄, try local search:
- Start from a good initial coloring (e.g., extend P(43) by adding vertex 44)
- Objective: minimize total monochromatic K₅ count
- Move: flip one edge color
- Use incremental K₅ counting for efficiency

```python
"""
Local search for Ramsey colorings.

Key insight: We don't need to find a GLOBAL optimum.
We need to find ANY coloring with K₅ count = 0.

This is a constraint satisfaction problem, not optimization.
But treating it as optimization (minimize violations) often works.
"""
```

Implement:
- `extend_paley_43_to_44() -> RamseyGraph`: Add vertex 44 to P(43), try different colorings for new edges
- `simulated_annealing(initial, max_steps, temp_schedule) -> RamseyGraph`
- `tabu_search(initial, max_steps, tabu_tenure) -> RamseyGraph`
- Track and log: steps, temperature, K₅ count over time

---

### Prompt 4.2: Hybrid Approach

Create `src/search/hybrid.py`:

Combine algebraic structure with local search:
1. Generate candidate colorings from near-Paley constructions
2. Perturb systematically
3. Apply local search to each

Also try:
- Multiple random restarts
- Different initial colorings from different algebraic families
- Population-based search (genetic algorithm on colorings)

---

### Prompt 4.3: Document Local Search Results

Run extensive local search experiments. Document:
- Best K₅ count achieved (if not zero)
- Which initial colorings led to best results
- Typical trajectory (K₅ count over iterations)
- Whether search gets stuck in local minima

If a valid coloring is found, verify exhaustively and export.

---

### Prompt 4.4: Test Scaling Hypothesis (Experimental)

**Background:** There is a hypothesis (from work on RL batch size schedules) that iterative stochastic algorithms exhibit phase transitions when a "computational effort" parameter scales as $B_k = C \cdot k^{2\gamma}$, where $\gamma$ is related to a "learning rate" decay schedule. We want to test whether this applies to Ramsey coloring local search.

**Operationalization for local search:**

Define the following parameters:
- **Iteration** $k$: The number of accepted moves so far
- **Evaluation budget** $B_k$: How many candidate edge-flips to evaluate before selecting the best one (or accepting probabilistically)
- **Cooling schedule** $T_k = T_0 / k^\gamma$: Temperature for simulated annealing acceptance probability

**Experiment design:**

1. **Baseline (fixed budget):** Run simulated annealing with fixed $B_k = B$ for various $B \in \{1, 10, 50, 100, 500\}$. For each, use standard cooling $T_k = T_0 / k^{0.5}$ (so $\gamma = 0.5$). Record:
   - Success rate (found valid coloring?)
   - Iterations to success (if successful)
   - Best K₅ count achieved (if unsuccessful)
   - Wall-clock time

2. **Adaptive budget (test hypothesis):** Run with $B_k = \max(1, \lfloor C \cdot k^p \rfloor)$ for:
   - $p \in \{0.5, 1.0, 1.5, 2.0, 2.5\}$ (testing around $p = 2\gamma = 1.0$)
   - $C \in \{0.1, 0.5, 1.0, 5.0\}$
   
   Use the same cooling schedule ($\gamma = 0.5$). Record same metrics.

3. **Analysis:** 
   - Is there a phase transition in success rate around $p = 2\gamma$?
   - Does the "3:1 gain ratio" appear (most improvement from below-threshold to threshold)?
   - Plot success rate vs. $p$ for fixed total compute budget

**What we're looking for:**
- If there IS a phase transition at $p \approx 2\gamma$: This suggests the RL scaling framework transfers to combinatorial search, which would be a novel theoretical connection worth investigating further.
- If there is NO phase transition: Document this negative result. The analogy may not hold, or may require different operationalization.

**Implementation notes:**
- "Evaluating" a candidate means computing the change in K₅ count if that edge were flipped (use incremental counting)
- "Selecting" means either greedy (take best) or probabilistic (Metropolis acceptance)
- Control for total compute: compare runs with equal total edge evaluations, not equal iterations

Create `experiments/scaling_hypothesis.py` with this experimental harness and `experiments/scaling_results.md` with analysis.

---

### Prompt 4.5: Document All Local Search Results

Consolidate results from Prompts 4.1-4.4. In `docs/approach_log.md`, create a comprehensive summary:

- Best K₅ count achieved across all methods (if not zero)
- Which initial colorings led to best results
- Typical trajectory (K₅ count over iterations)
- Whether search gets stuck in local minima
- Scaling hypothesis results: was there a phase transition? At what $p$?
- Computational cost comparison across methods

If a valid coloring is found, verify exhaustively and export to `colorings/`.

---

## Phase 5: SAT Solver Approach

### Prompt 5.1: SAT Encoding

Create `src/search/sat_encoding.py`:

The full K₄₄ problem is too large for SAT solvers without symmetry breaking.
But we can:
1. Encode partial constraints (e.g., fix some edges from algebraic construction)
2. Use symmetry-breaking predicates
3. Try incremental SAT (fix K₅-free subgraph, extend one vertex at a time)

```python
"""
SAT encoding for Ramsey coloring problems.

Variables: x_{ij} for each edge (i,j) with i < j
           True = blue, False = red

Constraints: For each 5-set {a,b,c,d,e}:
- NOT(all edges red): (x_ab OR x_ac OR ... OR x_de)  
- NOT(all edges blue): (NOT x_ab OR NOT x_ac OR ... OR NOT x_de)

For K_44: 946 variables, 2,172,016 clauses (each 5-set gives 2 clauses)
This is large but potentially tractable with modern SAT solvers.
"""
```

Implement:
- `encode_ramsey_sat(n, s, t) -> CNF`: Generate CNF for R(s,t) lower bound on K_n
- `add_symmetry_breaking(cnf, n)`: Lexicographic ordering constraints
- `add_partial_coloring(cnf, partial)`: Fix some edges
- Interface to PySAT or similar

---

### Prompt 5.2: Incremental SAT Strategy

Rather than encoding all of K₄₄:
1. Start with K₄₃ (we know P(43) works)
2. Add vertex 44 one edge at a time
3. At each step, check if current partial coloring extends

This is "SAT-based tree search" and may find a solution faster.

---

## Phase 6: Verification and Formalization

### Prompt 6.1: Generate Verification Certificate

If a valid coloring is found, create a certificate that can be independently verified:

```python
"""
A verification certificate for a (5,5)-free coloring consists of:
1. The coloring itself (n(n-1)/2 bits)
2. For each 5-set, evidence it's not monochromatic:
   - Red 5-sets: identify one blue edge
   - Blue 5-sets: identify one red edge

This certificate is O(n^5) in size but verifiable in O(n^5) time
with trivial code (just check each claimed "witness edge").
"""
```

Implement:
- `generate_certificate(coloring) -> Certificate`
- `verify_certificate(certificate) -> bool`: Simple, auditable verifier

---

### Prompt 6.2: Lean Formalization Setup

Set up the Lean project in `lean/`:

```lean
-- R55/Basic.lean
import Mathlib.Combinatorics.SimpleGraph.Basic
import Mathlib.Data.Fintype.Basic

/-- A 2-coloring of the complete graph on n vertices -/
def Coloring (n : ℕ) := Fin n → Fin n → Bool

/-- The coloring is symmetric (undirected graph) -/
def Coloring.symmetric {n : ℕ} (c : Coloring n) : Prop :=
  ∀ i j, c i j = c j i

/-- A set of 5 vertices forms a monochromatic clique in color b -/
def is_mono_k5 {n : ℕ} (c : Coloring n) (s : Finset (Fin n)) (b : Bool) : Prop :=
  s.card = 5 ∧ ∀ i ∈ s, ∀ j ∈ s, i ≠ j → c i j = b
```

Note: The actual formalization is nontrivial. The key insight is that for a computational result, we can:
1. Define the coloring as a computable function
2. Use `native_decide` or `decide` tactics to verify each 5-set
3. This is slow but produces a valid proof

---

### Prompt 6.3: Complete Lean Verification (If Valid Coloring Found)

If we have a valid coloring:
1. Encode the coloring as a Lean definition
2. State the theorem: "This coloring has no monochromatic K₅"
3. Prove by computation (check all 1,086,008 subsets)

This will take significant compile time but produces a machine-checked proof.

---

## Phase 7: Contingency - What If K₄₄ Fails?

### Prompt 7.1: Investigate Why K₄₄ Might Not Work

If all approaches fail to find a (5,5)-free coloring of K₄₄:

1. Document all approaches tried and their failure modes
2. Analyze: Do local minima have structure? What's the minimum K₅ count achieved?
3. Consider: Maybe R(5,5) = 44 (no valid coloring exists)?

This is also valuable research output.

---

### Prompt 7.2: Alternative Goals

If K₄₄ seems impossible:
1. **Strengthen K₄₃ verification**: Multiple independent constructions
2. **Upper bound work**: Try to prove R(5,5) ≤ 45 (would require different techniques)
3. **Parameter exploration**: What about R(5,6)? R(4,6)?

---

## Summary: Checkpoint Requirements

Before proceeding to the next phase, ensure:

**After Phase 1:**
- [ ] All tests pass
- [ ] Mathematical background document is complete
- [ ] Code is clean and documented

**After Phase 2:**
- [ ] P(43) verified as (5,5)-free
- [ ] Verification time documented
- [ ] Approach log started

**After Phase 3:**
- [ ] Circulant search completed
- [ ] Results (positive or negative) documented
- [ ] If valid coloring found, exported

**After Phase 4:**
- [ ] Local search experiments completed
- [ ] Best results documented
- [ ] If valid coloring found, exported and verified

**After Phase 5:**
- [ ] SAT approach attempted
- [ ] Results documented

**After Phase 6:**
- [ ] If valid coloring: certificate generated, Lean proof complete
- [ ] If no valid coloring: comprehensive documentation of attempts

---

## References

- Radziszowski, S. P. (2024). Small Ramsey Numbers. *Electronic Journal of Combinatorics*, Dynamic Survey.
- McKay, B. D., & Radziszowski, S. P. (1995). R(4,5) = 25. *Journal of Graph Theory*.
- Exoo, G. Various computational lower bounds on Ramsey numbers.
- Paley, R. E. A. C. (1933). On orthogonal matrices. *Journal of Mathematics and Physics*.

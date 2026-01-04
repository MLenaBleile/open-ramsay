# Mathematical Background: R(5,5) Lower Bound Problem

## 1. Definition of Ramsey Numbers

**Ramsey numbers** R(s,t) are fundamental constants in combinatorial mathematics. The Ramsey number R(s,t) is defined as:

> The minimum positive integer n such that any 2-coloring of the edges of the complete graph K_n contains either a monochromatic K_s (complete graph on s vertices) in the first color OR a monochromatic K_t in the second color.

**Existence**: Ramsey's theorem (1930) guarantees that R(s,t) exists for all positive integers s, t ≥ 2.

**Basic values**:
- R(2,k) = k (trivial)
- R(3,3) = 6 (the classic "party problem")
- R(4,4) = 18
- R(3,4) = 9, R(3,5) = 14, R(3,6) = 18

**Symmetric Ramsey numbers** R(k,k) are particularly difficult to compute:
- R(3,3) = 6 ✓
- R(4,4) = 18 ✓
- R(5,5) = ? (open problem)
- R(6,6) = ? (wide open)

## 2. Current State of R(5,5)

The best known bounds are:

**43 ≤ R(5,5) ≤ 46**

### Lower Bound: R(5,5) ≥ 43

The lower bound comes from constructing a 2-coloring of K₄₂ with no monochromatic K₅.

The **Paley graph** P(43) provides this construction:
- Consider the prime p = 43 (note: 43 ≡ 3 (mod 4))
- Actually, we use a modified construction since 43 ≡ 3 (mod 4)
- For p ≡ 1 (mod 4): edge (i,j) is red if (i-j) is a quadratic residue mod p
- For p ≡ 3 (mod 4): we use a slightly different construction

**Correction**: The Paley graph for prime q ≡ 1 (mod 4) is self-complementary. For q = 43 ≡ 3 (mod 4), the construction still works but requires the extended Paley graph or a modified approach.

The verified result is that there exists a (5,5)-free 2-coloring of K₄₂, hence R(5,5) ≥ 43.

### Upper Bound: R(5,5) ≤ 46

The upper bound of 46 was established by McKay and Radziszowski through computational methods, improving earlier bounds.

### The Open Question

**Does a (5,5)-free 2-coloring of K₄₃ exist?**

If yes: R(5,5) ≥ 44
If no: R(5,5) = 43

Our goal is to search for such a coloring.

## 3. Why K₄₄ is Hard

### 44 is Not Prime

The Paley graph construction requires a prime (or prime power) p ≡ 1 (mod 4). The number 44 = 4 × 11 is not prime, so no direct Paley construction exists.

### No Known Algebraic Construction

Unlike K₄₂ (which can be colored using P(43)'s structure), there is no known algebraic construction that produces a (5,5)-free coloring of K₄₃.

### Computational Barriers

Even if we try all possible 2-colorings:
- Number of edges in K₄₄: C(44,2) = 946
- Number of possible 2-colorings: 2^946 ≈ 10^285
- This is astronomically larger than the number of atoms in the observable universe (~10^80)

## 4. Computational Complexity

### Problem Size for K₄₄

| Parameter | Value |
|-----------|-------|
| Vertices | 44 |
| Edges | C(44,2) = 946 |
| Potential K₅ subgraphs | C(44,5) = 1,086,008 |
| 2-colorings | 2^946 ≈ 10^285 |

### Verification Complexity

Given a specific coloring, verification is polynomial:
- For each of the C(44,5) = 1,086,008 potential 5-cliques
- Check if all C(5,2) = 10 edges are the same color
- Total: O(n^5) operations

This is tractable: about 10^7 subset checks, each requiring 10 edge lookups.

### Search Complexity

Without structure, exhaustive search is impossible. Strategies to reduce the search space:

1. **Symmetry reduction**: If a coloring works, so do all automorphisms. Factor by the automorphism group.

2. **Algebraic structure**: Restrict to colorings with algebraic structure (circulant, Cayley, etc.)

3. **Local search**: Start from a good candidate and optimize

4. **SAT/SMT solvers**: Encode the constraint satisfaction problem

## 5. Key Structural Approaches

### 5.1 Circulant Graphs

A **circulant graph** C(n, S) has:
- Vertex set: {0, 1, ..., n-1}
- Edge (i,j) is red if min(|i-j|, n-|i-j|) ∈ S, blue otherwise

The **connection set** S ⊆ {1, 2, ..., ⌊n/2⌋} determines the coloring.

**Advantage**: Circulant graphs have n-fold rotational symmetry, reducing verification by factor of n.

**For n = 44**: Need S ⊆ {1, ..., 22}. With |S| ≈ 11 for balanced density, there are C(22,11) ≈ 705,432 candidate sets.

### 5.2 Cayley Graphs

A **Cayley graph** Cay(G, S) for group G and generating set S:
- Vertices: elements of G
- Edge (g, h) is red if g⁻¹h ∈ S

This generalizes circulant graphs (which are Cayley graphs over Z_n).

**For n = 44**: Could use G = Z₂ × Z₂₂, Z₄ × Z₁₁, etc.

### 5.3 Paley-like Constructions

Generalize the Paley graph idea:
- Use quadratic characters over finite fields or rings
- Extend to non-prime moduli using composite constructions
- Use character sums to estimate clique numbers

### 5.4 Local Search Methods

Since algebraic constructions may not suffice:

**Simulated Annealing**:
- Start from a good initial coloring (e.g., extend P(43))
- Objective: minimize count of monochromatic K₅
- Move: flip one edge color
- Accept moves probabilistically based on temperature

**Tabu Search**:
- Track recently flipped edges
- Prevent cycling back
- Allow non-improving moves to escape local minima

**Hybrid**: Combine algebraic start with local refinement

### 5.5 SAT/SMT Encoding

Encode as Boolean satisfiability:
- Variable x_{ij} for each edge (True=blue, False=red)
- For each 5-set {a,b,c,d,e}:
  - Clause: (x_ab ∨ x_ac ∨ ... ∨ x_de) - not all red
  - Clause: (¬x_ab ∨ ¬x_ac ∨ ... ∨ ¬x_de) - not all blue

For K₄₄: 946 variables, 2 × 1,086,008 = 2,172,016 clauses.

**Symmetry breaking**: Add constraints to eliminate symmetric solutions.

## 6. References

1. **Radziszowski, S. P.** (2024). Small Ramsey Numbers. *Electronic Journal of Combinatorics*, Dynamic Survey DS1.
   - The authoritative reference for known Ramsey number bounds
   - Updated periodically with new results

2. **McKay, B. D., & Radziszowski, S. P.** (1995). R(4,5) = 25. *Journal of Graph Theory*, 19(3), 309-322.
   - Computational determination of R(4,5)
   - Methods applicable to R(5,5) upper bounds

3. **Exoo, G.** Various computational lower bounds.
   - Systematic computational search for Ramsey colorings
   - http://ginger.indstate.edu/ge/RAMSEY/

4. **Paley, R. E. A. C.** (1933). On orthogonal matrices. *Journal of Mathematics and Physics*, 12, 311-320.
   - Original Paley graph construction
   - Foundation for algebraic Ramsey constructions

5. **Graham, R. L., Rothschild, B. L., & Spencer, J. H.** (1990). *Ramsey Theory* (2nd ed.). Wiley-Interscience.
   - Comprehensive textbook treatment
   - Probabilistic and constructive methods

6. **Bohman, T., & Keevash, P.** (2010). The early evolution of the H-free process. *Inventiones mathematicae*, 181(2), 291-336.
   - Modern probabilistic methods for Ramsey bounds

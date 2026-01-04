# Approach Log: R(5,5) ≥ 44 Investigation

This document tracks all approaches attempted, their results, and lessons learned.

---

## Log Format

Each entry should include:
- **Date**: When the experiment was run
- **Approach**: Description of the method
- **Parameters**: Specific settings used
- **Result**: What happened
- **Runtime**: How long it took
- **Analysis**: What we learned
- **Next Steps**: What to try based on this

---

## Phase 2: Verification of Known Results

### Entry 2.1: Paley Graph Survey

**Date**: 2026-01-04

**Approach**: Survey all Paley graphs P(p) for primes p ≤ 47 to determine which are (5,5)-free.

**Parameters**:
- Tested primes: 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47
- Used standard Paley construction: edge (i,j) colored by whether (j-i) mod p is a QR

**Result**:

| Prime p | p mod 4 | (5,5)-free? | Red K₅s | Blue K₅s |
|---------|---------|-------------|---------|----------|
| 5 | 1 | ✓ Yes | 0 | 0 |
| 7 | 3 | ✓ Yes | 0 | 0 |
| 11 | 3 | ✓ Yes | 0 | 0 |
| 13 | 1 | ✓ Yes | 0 | 0 |
| 17 | 1 | ✓ Yes | 0 | 0 |
| 19 | 3 | ✓ Yes | 0 | 0 |
| 23 | 3 | ✗ No | 3 | 121 |
| 29 | 1 | ✓ Yes | 0 | 0 |
| 31 | 3 | ✗ No | 7 | 534 |
| 37 | 1 | ✓ Yes | 0 | 0 |
| 41 | 1 | ✗ No | 205 | 205 |
| 43 | 3 | ✗ No | 316 | 1064 |

**Runtime**: ~6.5 seconds for full survey

**Analysis**:
1. **P(37) is the largest (5,5)-free Paley graph** - This proves R(5,5) ≥ 38 from Paley construction alone.
2. **P(43) is NOT (5,5)-free** - Contrary to initial assumption, the Paley graph on 43 vertices has 316 red K₅s and 1064 blue K₅s.
3. **The R(5,5) ≥ 43 bound must come from a different construction** - Likely a circulant graph found computationally.
4. **Pattern observation**: For p ≡ 1 (mod 4), Paley graphs tend to have balanced K₅ counts when they fail (e.g., P(41) has 205 of each).

**Next Steps**:
1. Implement circulant graph constructions
2. Search for (5,5)-free circulant graphs on 42+ vertices
3. Research the actual construction used for R(5,5) ≥ 43

---

### Entry 2.2: P(37) Verification

**Date**: 2026-01-04

**Approach**: Exhaustively verify that P(37) contains no monochromatic K₅.

**Parameters**:
- n = 37 vertices
- C(37,5) = 435,897 potential 5-subsets checked

**Result**: ✓ **P(37) is (5,5)-free**

**Runtime**: ~0.5 seconds

**Analysis**: This confirms R(5,5) ≥ 38. To prove R(5,5) ≥ 43, we need colorings of K₃₈ through K₄₂.

---

## Phase 3: Circulant Search

### Entry 3.1: Exhaustive Circulant Search for n=44

**Date**: [To be filled]

**Approach**: Search over all connection sets S ⊆ {1,...,22} for valid circulant colorings.

**Parameters**: [To be filled]

**Result**: [To be filled]

**Runtime**: [To be filled]

**Analysis**: [To be filled]

---

## Phase 4: Local Search

### Entry 4.1: Simulated Annealing from Extended P(37)

**Date**: [To be filled]

**Approach**: [To be filled]

**Result**: [To be filled]

---

## Summary Statistics

| Approach | Attempts | Best K₅ Count | Valid Colorings Found |
|----------|----------|---------------|----------------------|
| Paley P(37) | 1 | 0 | 1 (verified) |
| Paley P(43) | 1 | 1380 | 0 (not valid) |
| Circulant n=44 | - | - | - |
| Local Search | - | - | - |
| SAT Solver | - | - | - |

## Key Insights

1. **Paley construction limit**: The Paley graph construction provides (5,5)-free colorings only up to n=37.
2. **Gap to close**: We need to find (5,5)-free colorings for n = 38, 39, 40, 41, 42, and 43 to prove R(5,5) ≥ 44.
3. **Computational approach needed**: Unlike smaller Ramsey numbers, R(5,5) bounds require computational search rather than pure algebraic constructions.

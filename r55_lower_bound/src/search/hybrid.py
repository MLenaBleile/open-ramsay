"""
Hybrid search combining algebraic structure with local search.

Strategies:
1. Generate candidate colorings from near-Paley constructions
2. Perturb systematically
3. Apply local search to each

Also implements:
- Multiple random restarts
- Different initial colorings from different algebraic families
- Population-based search (simple genetic algorithm)
"""

from typing import Optional, List, Tuple, Callable
import numpy as np
import time
import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5_total, verify_k5_free
from src.constructions.paley import paley_coloring, get_paley_like_connection_set
from src.constructions.circulant import circulant_coloring
from src.search.local_search import (
    simulated_annealing,
    tabu_search,
    greedy_descent,
    SearchResult,
)


def perturb_coloring(
    graph: RamseyGraph,
    num_flips: int,
    seed: Optional[int] = None
) -> RamseyGraph:
    """
    Create a perturbation of a coloring by flipping random edges.

    Args:
        graph: Base coloring
        num_flips: Number of edges to flip
        seed: Random seed for reproducibility

    Returns:
        New RamseyGraph with perturbation applied
    """
    if seed is not None:
        np.random.seed(seed)

    result = graph.copy()
    n = result.n
    num_edges = n * (n - 1) // 2

    # Choose random edges to flip
    flipped = set()
    while len(flipped) < num_flips:
        idx = np.random.randint(num_edges)
        flipped.add(idx)

    # Apply flips
    for idx in flipped:
        result.edges[idx] = not result.edges[idx]

    return result


def near_paley_constructions(n: int, num_variants: int = 10) -> List[RamseyGraph]:
    """
    Generate near-Paley constructions for n vertices.

    Uses Paley-like connection sets with small perturbations.

    Args:
        n: Number of vertices
        num_variants: Number of variants to generate

    Returns:
        List of candidate colorings
    """
    candidates = []

    # Find closest prime for Paley-like set
    primes = [p for p in [37, 41, 43, 47] if p <= n + 10]

    for p in primes:
        base_set = get_paley_like_connection_set(p)

        # Adapt to n
        max_dist = n // 2
        adapted_set = {d for d in base_set if d <= max_dist}

        # Generate variants by adding/removing elements
        variants_generated = 0

        # Original
        if len(adapted_set) > 0:
            candidates.append(circulant_coloring(n, adapted_set))
            variants_generated += 1

        # With one element added
        for d in range(1, max_dist + 1):
            if d not in adapted_set and variants_generated < num_variants:
                new_set = adapted_set | {d}
                candidates.append(circulant_coloring(n, new_set))
                variants_generated += 1

        # With one element removed
        for d in list(adapted_set):
            if variants_generated < num_variants:
                new_set = adapted_set - {d}
                if len(new_set) > 0:
                    candidates.append(circulant_coloring(n, new_set))
                    variants_generated += 1

    return candidates[:num_variants]


def hybrid_search(
    n: int,
    max_time: float = 120.0,
    num_algebraic: int = 10,
    num_random: int = 5,
    perturbation_range: Tuple[int, int] = (5, 20),
    verbose: bool = True
) -> SearchResult:
    """
    Hybrid search combining algebraic starts with local refinement.

    Args:
        n: Number of vertices
        max_time: Maximum time in seconds
        num_algebraic: Number of algebraic starting points
        num_random: Number of random starting points
        perturbation_range: Range of perturbation sizes
        verbose: Print progress

    Returns:
        Best SearchResult found
    """
    start_time = time.time()
    best_result = None

    # Phase 1: Try algebraic constructions
    if verbose:
        print("Phase 1: Algebraic constructions...")

    algebraic_starts = near_paley_constructions(n, num_algebraic)

    for i, graph in enumerate(algebraic_starts):
        if time.time() - start_time > max_time:
            break

        k5 = count_mono_k5_total(graph)
        if verbose:
            print(f"  Algebraic {i+1}: k5={k5}")

        if k5 == 0:
            return SearchResult(
                graph=graph, k5_count=0, iterations=0,
                elapsed_time=time.time() - start_time,
                history=[0], found_valid=True
            )

        # Apply greedy descent
        result = greedy_descent(graph.copy(), max_steps=5000)
        if best_result is None or result.k5_count < best_result.k5_count:
            best_result = result

        if result.found_valid:
            return result

    # Phase 2: Perturb best algebraic and search
    if verbose:
        print("Phase 2: Perturbed algebraic with local search...")

    if best_result is not None:
        base_graph = best_result.graph

        for perturbation in range(perturbation_range[0], perturbation_range[1], 2):
            if time.time() - start_time > max_time:
                break

            for trial in range(3):
                if time.time() - start_time > max_time:
                    break

                perturbed = perturb_coloring(base_graph, perturbation)
                result = simulated_annealing(
                    perturbed, max_steps=10000,
                    initial_temp=5.0, cooling_rate=0.999
                )

                if result.k5_count < best_result.k5_count:
                    best_result = result
                    if verbose:
                        print(f"  Improved: k5={result.k5_count} (perturbation={perturbation})")

                if result.found_valid:
                    return result

    # Phase 3: Random starts with simulated annealing
    if verbose:
        print("Phase 3: Random starts...")

    for i in range(num_random):
        if time.time() - start_time > max_time:
            break

        graph = RamseyGraph(n)
        for idx in range(n * (n - 1) // 2):
            graph.edges[idx] = np.random.random() < 0.5

        result = simulated_annealing(
            graph, max_steps=20000,
            initial_temp=10.0, cooling_rate=0.9995
        )

        if best_result is None or result.k5_count < best_result.k5_count:
            best_result = result
            if verbose:
                print(f"  Random {i+1}: k5={result.k5_count}")

        if result.found_valid:
            return result

    if best_result is None:
        # No result at all - create a dummy
        graph = RamseyGraph(n)
        best_result = SearchResult(
            graph=graph, k5_count=count_mono_k5_total(graph),
            iterations=0, elapsed_time=time.time() - start_time,
            history=[], found_valid=False
        )

    return best_result


def genetic_search(
    n: int,
    population_size: int = 20,
    generations: int = 100,
    mutation_rate: float = 0.02,
    elite_size: int = 2,
    verbose: bool = True
) -> SearchResult:
    """
    Simple genetic algorithm for Ramsey coloring.

    Args:
        n: Number of vertices
        population_size: Size of population
        generations: Number of generations
        mutation_rate: Probability of flipping each edge
        elite_size: Number of best individuals to preserve
        verbose: Print progress

    Returns:
        Best SearchResult found
    """
    start_time = time.time()
    num_edges = n * (n - 1) // 2

    # Initialize population
    population = []
    for _ in range(population_size):
        graph = RamseyGraph(n)
        for idx in range(num_edges):
            graph.edges[idx] = np.random.random() < 0.5
        fitness = -count_mono_k5_total(graph)  # Negative because we want to maximize
        population.append((fitness, graph))

    history = []
    best_ever = None

    for gen in range(generations):
        # Sort by fitness (descending)
        population.sort(key=lambda x: x[0], reverse=True)

        best_fitness = population[0][0]
        best_k5 = -best_fitness
        history.append(best_k5)

        if best_ever is None or best_fitness > best_ever[0]:
            best_ever = (best_fitness, population[0][1].copy())

        if verbose and gen % 10 == 0:
            print(f"Gen {gen}: best k5={best_k5}")

        if best_k5 == 0:
            break

        # Selection and reproduction
        new_population = []

        # Elite - keep best unchanged
        for i in range(elite_size):
            new_population.append((population[i][0], population[i][1].copy()))

        # Generate rest through crossover and mutation
        while len(new_population) < population_size:
            # Tournament selection
            idx1 = max(np.random.randint(population_size // 2),
                      np.random.randint(population_size // 2))
            idx2 = max(np.random.randint(population_size // 2),
                      np.random.randint(population_size // 2))

            parent1 = population[idx1][1]
            parent2 = population[idx2][1]

            # Crossover
            child = RamseyGraph(n)
            crossover_point = np.random.randint(num_edges)
            for idx in range(num_edges):
                if idx < crossover_point:
                    child.edges[idx] = parent1.edges[idx]
                else:
                    child.edges[idx] = parent2.edges[idx]

            # Mutation
            for idx in range(num_edges):
                if np.random.random() < mutation_rate:
                    child.edges[idx] = not child.edges[idx]

            fitness = -count_mono_k5_total(child)
            new_population.append((fitness, child))

        population = new_population

    elapsed = time.time() - start_time
    best_graph = best_ever[1] if best_ever else population[0][1]
    best_k5 = -best_ever[0] if best_ever else -population[0][0]

    return SearchResult(
        graph=best_graph,
        k5_count=best_k5,
        iterations=generations,
        elapsed_time=elapsed,
        history=history,
        found_valid=(best_k5 == 0)
    )


def combined_search(
    n: int,
    time_limit: float = 300.0,
    verbose: bool = True
) -> Optional[RamseyGraph]:
    """
    Combined search using all available methods.

    Args:
        n: Number of vertices
        time_limit: Maximum time in seconds
        verbose: Print progress

    Returns:
        Valid RamseyGraph if found, None otherwise
    """
    start_time = time.time()

    # Try hybrid search first
    if verbose:
        print(f"=== Combined search for n={n} ===")
        print("\n1. Hybrid search...")

    result = hybrid_search(n, max_time=time_limit * 0.4, verbose=verbose)

    if result.found_valid:
        if verbose:
            print(f"Found valid coloring in hybrid search!")
        return result.graph

    if verbose:
        print(f"Hybrid best: k5={result.k5_count}")

    # Try genetic algorithm
    remaining = time_limit - (time.time() - start_time)
    if remaining > 30:
        if verbose:
            print("\n2. Genetic algorithm...")

        gens = max(50, int(remaining / 2))
        result2 = genetic_search(n, generations=gens, verbose=verbose)

        if result2.found_valid:
            if verbose:
                print(f"Found valid coloring in genetic search!")
            return result2.graph

        if result2.k5_count < result.k5_count:
            result = result2
            if verbose:
                print(f"Genetic improved: k5={result.k5_count}")

    # Final intensive local search on best
    remaining = time_limit - (time.time() - start_time)
    if remaining > 10:
        if verbose:
            print("\n3. Intensive local search on best...")

        result3 = tabu_search(result.graph.copy(), max_steps=int(remaining * 1000))

        if result3.found_valid:
            if verbose:
                print(f"Found valid coloring in tabu search!")
            return result3.graph

    return None

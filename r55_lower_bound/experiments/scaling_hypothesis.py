"""
Experiment: Test Scaling Hypothesis for Local Search

Background: There is a hypothesis that iterative stochastic algorithms
exhibit phase transitions when a "computational effort" parameter scales
as B_k = C * k^(2*gamma), where gamma is related to the cooling schedule.

This experiment tests whether this applies to Ramsey coloring local search.

Operationalization:
- Iteration k: Number of accepted moves so far
- Evaluation budget B_k: How many candidate edge-flips to evaluate
- Cooling schedule T_k = T_0 / k^gamma

Experiment design:
1. Baseline (fixed budget): Run with fixed B for various B values
2. Adaptive budget: Run with B_k = max(1, floor(C * k^p))
3. Analysis: Look for phase transition around p = 2*gamma
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import time
import json
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.core.graph import RamseyGraph
from src.core.clique_checker import count_mono_k5_total, check_edge_flip_delta


@dataclass
class ExperimentResult:
    """Result of a single experiment run."""
    method: str
    n: int
    success: bool
    iterations_to_success: Optional[int]
    best_k5: int
    total_evaluations: int
    wall_clock_time: float
    parameters: Dict


def simulated_annealing_with_budget(
    graph: RamseyGraph,
    max_iterations: int,
    initial_temp: float,
    gamma: float,
    budget_mode: str,  # 'fixed', 'adaptive'
    fixed_budget: int = 10,
    adaptive_c: float = 1.0,
    adaptive_p: float = 1.0,
    verbose: bool = False
) -> ExperimentResult:
    """
    Simulated annealing with configurable evaluation budget.

    Args:
        graph: Initial coloring (will be modified)
        max_iterations: Maximum accepted moves
        initial_temp: T_0 in cooling schedule T_k = T_0 / k^gamma
        gamma: Exponent in cooling schedule
        budget_mode: 'fixed' or 'adaptive'
        fixed_budget: B for fixed mode
        adaptive_c: C in B_k = C * k^p
        adaptive_p: p in B_k = C * k^p
        verbose: Print progress

    Returns:
        ExperimentResult with metrics
    """
    start_time = time.time()

    n = graph.n
    num_edges = n * (n - 1) // 2

    current_k5 = count_mono_k5_total(graph)
    best_k5 = current_k5
    best_graph = graph.copy()

    total_evaluations = 0
    accepted_moves = 0

    for k in range(1, max_iterations + 1):
        if current_k5 == 0:
            break

        # Compute temperature
        temp = initial_temp / (k ** gamma)
        if temp < 1e-10:
            temp = 1e-10

        # Compute budget
        if budget_mode == 'fixed':
            budget = fixed_budget
        else:  # adaptive
            budget = max(1, int(adaptive_c * (k ** adaptive_p)))

        # Evaluate 'budget' random edge flips
        best_delta = float('inf')
        best_edge = None

        for _ in range(budget):
            # Pick random edge
            idx = np.random.randint(num_edges)
            i, j = 0, 0
            remaining = idx
            for ii in range(n):
                edges_from_ii = n - ii - 1
                if remaining < edges_from_ii:
                    i = ii
                    j = ii + 1 + remaining
                    break
                remaining -= edges_from_ii

            delta = check_edge_flip_delta(graph, (i, j))
            total_evaluations += 1

            if delta < best_delta:
                best_delta = delta
                best_edge = (i, j)

        # Metropolis acceptance
        if best_edge is not None:
            if best_delta <= 0:
                accept = True
            else:
                prob = np.exp(-best_delta / temp)
                accept = np.random.random() < prob

            if accept:
                graph.flip_edge(*best_edge)
                current_k5 += best_delta
                accepted_moves += 1

                if current_k5 < best_k5:
                    best_k5 = current_k5
                    best_graph = graph.copy()

        if verbose and k % 1000 == 0:
            print(f"  k={k}: k5={current_k5}, best={best_k5}, temp={temp:.4f}, budget={budget}")

    elapsed = time.time() - start_time

    params = {
        'initial_temp': initial_temp,
        'gamma': gamma,
        'budget_mode': budget_mode,
    }
    if budget_mode == 'fixed':
        params['fixed_budget'] = fixed_budget
    else:
        params['adaptive_c'] = adaptive_c
        params['adaptive_p'] = adaptive_p

    return ExperimentResult(
        method='annealing_with_budget',
        n=n,
        success=(best_k5 == 0),
        iterations_to_success=accepted_moves if best_k5 == 0 else None,
        best_k5=best_k5,
        total_evaluations=total_evaluations,
        wall_clock_time=elapsed,
        parameters=params
    )


def run_baseline_experiment(
    n: int,
    num_trials: int = 10,
    max_iterations: int = 10000,
    gamma: float = 0.5,
    budgets: List[int] = [1, 10, 50, 100, 500],
    verbose: bool = True
) -> Dict[int, List[ExperimentResult]]:
    """
    Run baseline experiment with fixed evaluation budgets.

    Args:
        n: Number of vertices
        num_trials: Number of trials per budget
        max_iterations: Max accepted moves per trial
        gamma: Cooling schedule exponent
        budgets: List of fixed budgets to test

    Returns:
        Dictionary mapping budget to list of results
    """
    results = {b: [] for b in budgets}

    for budget in budgets:
        if verbose:
            print(f"\nTesting fixed budget B={budget}")

        for trial in range(num_trials):
            # Random initial coloring
            graph = RamseyGraph(n)
            for idx in range(n * (n - 1) // 2):
                graph.edges[idx] = np.random.random() < 0.5

            result = simulated_annealing_with_budget(
                graph,
                max_iterations=max_iterations,
                initial_temp=10.0,
                gamma=gamma,
                budget_mode='fixed',
                fixed_budget=budget,
                verbose=False
            )

            results[budget].append(result)

            if verbose:
                status = "SUCCESS" if result.success else f"k5={result.best_k5}"
                print(f"  Trial {trial+1}: {status}, evals={result.total_evaluations}")

    return results


def run_adaptive_experiment(
    n: int,
    num_trials: int = 10,
    max_iterations: int = 10000,
    gamma: float = 0.5,
    p_values: List[float] = [0.5, 1.0, 1.5, 2.0, 2.5],
    c_values: List[float] = [0.1, 0.5, 1.0, 5.0],
    verbose: bool = True
) -> Dict[Tuple[float, float], List[ExperimentResult]]:
    """
    Run adaptive budget experiment.

    Args:
        n: Number of vertices
        num_trials: Trials per (p, C) pair
        max_iterations: Max accepted moves per trial
        gamma: Cooling schedule exponent
        p_values: Exponents to test (hypothesis: transition at p = 2*gamma)
        c_values: Constants to test

    Returns:
        Dictionary mapping (p, C) to list of results
    """
    results = {}

    for p in p_values:
        for c in c_values:
            key = (p, c)
            results[key] = []

            if verbose:
                print(f"\nTesting adaptive p={p}, C={c}")

            for trial in range(num_trials):
                graph = RamseyGraph(n)
                for idx in range(n * (n - 1) // 2):
                    graph.edges[idx] = np.random.random() < 0.5

                result = simulated_annealing_with_budget(
                    graph,
                    max_iterations=max_iterations,
                    initial_temp=10.0,
                    gamma=gamma,
                    budget_mode='adaptive',
                    adaptive_c=c,
                    adaptive_p=p,
                    verbose=False
                )

                results[key].append(result)

                if verbose:
                    status = "SUCCESS" if result.success else f"k5={result.best_k5}"
                    print(f"  Trial {trial+1}: {status}, evals={result.total_evaluations}")

    return results


def analyze_results(
    baseline: Dict[int, List[ExperimentResult]],
    adaptive: Dict[Tuple[float, float], List[ExperimentResult]],
    gamma: float
) -> str:
    """
    Analyze experimental results and produce summary.

    Args:
        baseline: Results from baseline experiment
        adaptive: Results from adaptive experiment
        gamma: The gamma value used

    Returns:
        Markdown-formatted analysis
    """
    lines = ["# Scaling Hypothesis Experiment Results\n"]

    lines.append(f"## Parameters")
    lines.append(f"- Cooling schedule: T_k = T_0 / k^{gamma}")
    lines.append(f"- Predicted transition point: p = 2*gamma = {2*gamma}")
    lines.append("")

    # Baseline analysis
    lines.append("## Baseline Results (Fixed Budget)")
    lines.append("")
    lines.append("| Budget B | Success Rate | Avg Best K5 | Avg Evaluations |")
    lines.append("|----------|--------------|-------------|-----------------|")

    for budget in sorted(baseline.keys()):
        results = baseline[budget]
        success_rate = sum(1 for r in results if r.success) / len(results)
        avg_k5 = np.mean([r.best_k5 for r in results])
        avg_evals = np.mean([r.total_evaluations for r in results])
        lines.append(f"| {budget} | {success_rate:.2f} | {avg_k5:.1f} | {avg_evals:.0f} |")

    lines.append("")

    # Adaptive analysis
    lines.append("## Adaptive Results")
    lines.append("")

    # Group by p
    p_values = sorted(set(k[0] for k in adaptive.keys()))
    c_values = sorted(set(k[1] for k in adaptive.keys()))

    lines.append("### Success Rate by (p, C)")
    lines.append("")
    header = "| p \\ C |" + "|".join(f" {c} " for c in c_values) + "|"
    lines.append(header)
    lines.append("|" + "|".join(["---"] * (len(c_values) + 1)) + "|")

    for p in p_values:
        row = f"| {p} |"
        for c in c_values:
            results = adaptive.get((p, c), [])
            if results:
                success_rate = sum(1 for r in results if r.success) / len(results)
                row += f" {success_rate:.2f} |"
            else:
                row += " - |"
        lines.append(row)

    lines.append("")

    # Analysis
    lines.append("## Analysis")
    lines.append("")

    # Check for phase transition
    critical_p = 2 * gamma

    # Find success rates at different p values
    avg_success_by_p = {}
    for p in p_values:
        successes = []
        for c in c_values:
            results = adaptive.get((p, c), [])
            if results:
                successes.extend([r.success for r in results])
        if successes:
            avg_success_by_p[p] = sum(successes) / len(successes)

    lines.append("### Success Rate vs p (averaged over C)")
    for p, rate in sorted(avg_success_by_p.items()):
        marker = " <-- predicted transition" if abs(p - critical_p) < 0.1 else ""
        lines.append(f"- p={p}: {rate:.2f}{marker}")

    lines.append("")

    # Check for 3:1 gain ratio
    if len(avg_success_by_p) >= 2:
        p_list = sorted(avg_success_by_p.keys())
        gains = []
        for i in range(len(p_list) - 1):
            p1, p2 = p_list[i], p_list[i+1]
            gain = avg_success_by_p[p2] - avg_success_by_p[p1]
            gains.append((p1, p2, gain))
            lines.append(f"- Gain from p={p1} to p={p2}: {gain:.3f}")

    lines.append("")
    lines.append("### Conclusions")
    lines.append("")

    # Determine if there's a phase transition
    if avg_success_by_p:
        max_p = max(avg_success_by_p.keys(), key=lambda p: avg_success_by_p[p])
        if abs(max_p - critical_p) < 0.5:
            lines.append(f"**Phase transition observed near p={max_p} (predicted: {critical_p})**")
            lines.append("")
            lines.append("This suggests the RL scaling framework may transfer to combinatorial search.")
        else:
            lines.append(f"**Peak performance at p={max_p}, not at predicted p={critical_p}**")
            lines.append("")
            lines.append("The phase transition hypothesis may not hold in this context,")
            lines.append("or may require different operationalization.")
    else:
        lines.append("Insufficient data for analysis.")

    return "\n".join(lines)


def run_full_experiment(
    n: int = 15,
    num_trials: int = 5,
    max_iterations: int = 5000,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> str:
    """
    Run the full scaling hypothesis experiment.

    Args:
        n: Number of vertices (smaller = faster)
        num_trials: Trials per configuration
        max_iterations: Max iterations per trial
        output_file: Optional file to save results
        verbose: Print progress

    Returns:
        Markdown analysis
    """
    gamma = 0.5
    np.random.seed(42)

    if verbose:
        print(f"Running scaling hypothesis experiment (n={n})")
        print("=" * 50)

    # Baseline
    if verbose:
        print("\n=== BASELINE EXPERIMENT ===")
    baseline = run_baseline_experiment(
        n=n, num_trials=num_trials, max_iterations=max_iterations,
        gamma=gamma, budgets=[1, 10, 50, 100],
        verbose=verbose
    )

    # Adaptive
    if verbose:
        print("\n=== ADAPTIVE EXPERIMENT ===")
    adaptive = run_adaptive_experiment(
        n=n, num_trials=num_trials, max_iterations=max_iterations,
        gamma=gamma,
        p_values=[0.5, 1.0, 1.5, 2.0],
        c_values=[0.1, 1.0, 5.0],
        verbose=verbose
    )

    # Analysis
    analysis = analyze_results(baseline, adaptive, gamma)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(analysis)

    return analysis


if __name__ == "__main__":
    # Run a quick experiment
    analysis = run_full_experiment(
        n=12,  # Smaller for quick testing
        num_trials=3,
        max_iterations=2000,
        verbose=True
    )
    print("\n" + "=" * 50)
    print(analysis)

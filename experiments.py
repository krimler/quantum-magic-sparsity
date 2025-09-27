# experiments.py
"""
Magic Sparsity in QAOA: Experimental Validation
Benchmarks T-count and routing overhead for QAOA on random regular graphs
"""

import numpy as np
import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from dataclasses import dataclass
import json

@dataclass
class QAOACircuitStats:
    """Statistics for a QAOA circuit implementation"""
    n_qubits: int
    p_rounds: int
    n_edges: int
    n_rotations: int  # Total parameterized rotations
    t_count_logical: int  # T-gates for logical circuit
    clifford_count_logical: int  # Clifford gates (CNOT, H, S)
    total_gates_logical: int
    swap_count_1d: int  # SWAPs for 1D routing
    swap_count_2d: int  # SWAPs for 2D routing
    total_gates_1d: int
    total_gates_2d: int
    magic_fraction_logical: float
    magic_fraction_1d: float
    magic_fraction_2d: float

def generate_random_regular_graph(n: int, d: int, seed: int = None) -> nx.Graph:
    """Generate a random d-regular graph on n vertices"""
    if seed is not None:
        np.random.seed(seed)
    
    # For small n, d must satisfy n*d is even and d < n
    if (n * d) % 2 != 0:
        raise ValueError(f"n*d must be even for regular graphs (n={n}, d={d})")
    if d >= n:
        raise ValueError(f"Degree d must be less than n (d={d}, n={n})")
    
    return nx.random_regular_graph(d, n, seed=seed)

def count_qaoa_rotations(graph: nx.Graph, p: int) -> Dict[str, int]:
    """Count rotations in QAOA circuit"""
    n_vertices = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    
    return {
        'zz_rotations': p * n_edges,  # One per edge per round
        'x_rotations': p * n_vertices,  # One per vertex per round
        'total_rotations': p * (n_edges + n_vertices)
    }

def synthesize_rotation_t_count(precision_bits: int) -> int:
    """
    Estimate T-count for synthesizing a rotation to given precision.
    Using Solovay-Kitaev: T-count ≈ 3.97 * log(1/ε)
    For ε = 2^(-precision_bits), this gives ≈ 3.97 * precision_bits
    """
    # Simplified model: each rotation needs O(log(1/ε)) T-gates
    # For practical purposes, use ~3-4 T-gates per precision bit
    return int(4 * precision_bits)

def compute_precision_requirement(n: int, total_rotations: int) -> int:
    """
    Compute per-gate precision for total error 1/poly(n).
    Target total error: ε_total = 1/n²
    Per-gate error: ε_gate = ε_total / total_rotations
    Precision bits: -log₂(ε_gate)
    """
    total_error = 1.0 / (n * n)
    per_gate_error = total_error / total_rotations
    precision_bits = int(np.ceil(-np.log2(per_gate_error)))
    return precision_bits

def count_logical_gates(graph: nx.Graph, p: int, precision_bits: int) -> Dict[str, int]:
    """Count gates in logical QAOA circuit (no routing)"""
    rotation_counts = count_qaoa_rotations(graph, p)
    t_per_rotation = synthesize_rotation_t_count(precision_bits)
    
    # Each ZZ rotation: 2 CNOTs + rotation
    # Each X rotation: just rotation
    cnot_count = 2 * rotation_counts['zz_rotations']
    
    # T-gates from all rotations
    t_count = rotation_counts['total_rotations'] * t_per_rotation
    
    # Initial Hadamards
    h_count = graph.number_of_nodes()
    
    # Total Clifford gates (CNOTs + Hadamards + stabilizer part of rotations)
    # Each synthesized rotation has ~2*precision_bits Clifford gates
    clifford_from_synthesis = rotation_counts['total_rotations'] * 2 * precision_bits
    clifford_count = cnot_count + h_count + clifford_from_synthesis
    
    return {
        't_count': t_count,
        'clifford_count': clifford_count,
        'total_gates': t_count + clifford_count
    }

def route_to_1d_chain(graph: nx.Graph) -> int:
    """
    Estimate SWAP count for implementing graph on 1D chain.
    Simple model: each non-adjacent edge needs O(distance) SWAPs
    """
    n = graph.number_of_nodes()
    
    # Map vertices to 1D positions
    positions = {i: i for i in range(n)}
    
    total_swaps = 0
    for u, v in graph.edges():
        distance = abs(positions[u] - positions[v])
        if distance > 1:
            # Need (distance - 1) SWAPs to bring qubits together
            total_swaps += (distance - 1)
    
    return total_swaps

def route_to_2d_grid(graph: nx.Graph) -> int:
    """
    Estimate SWAP count for implementing graph on 2D grid.
    Map to sqrt(n) × sqrt(n) grid
    """
    n = graph.number_of_nodes()
    grid_size = int(np.ceil(np.sqrt(n)))
    
    # Map vertices to 2D grid positions
    positions = {}
    for i in range(n):
        row = i // grid_size
        col = i % grid_size
        positions[i] = (row, col)
    
    total_swaps = 0
    for u, v in graph.edges():
        u_pos = positions[u]
        v_pos = positions[v]
        manhattan_distance = abs(u_pos[0] - v_pos[0]) + abs(u_pos[1] - v_pos[1])
        if manhattan_distance > 1:
            # Need (manhattan_distance - 1) SWAPs
            total_swaps += (manhattan_distance - 1)
    
    return total_swaps

def analyze_qaoa_circuit(n: int, d: int, p: int, seed: int = None) -> QAOACircuitStats:
    """Complete analysis of QAOA circuit statistics"""
    
    # Generate graph
    graph = generate_random_regular_graph(n, d, seed)
    
    # Count rotations
    rotation_counts = count_qaoa_rotations(graph, p)
    total_rotations = rotation_counts['total_rotations']
    
    # Determine precision requirement
    precision_bits = compute_precision_requirement(n, total_rotations)
    
    # Count logical gates
    logical_gates = count_logical_gates(graph, p, precision_bits)
    
    # Estimate routing overhead
    swaps_1d = route_to_1d_chain(graph) * p  # Per round
    swaps_2d = route_to_2d_grid(graph) * p
    
    # Each SWAP = 3 CNOTs
    swap_gates_1d = swaps_1d * 3
    swap_gates_2d = swaps_2d * 3
    
    # Total gates including routing
    total_gates_1d = logical_gates['total_gates'] + swap_gates_1d
    total_gates_2d = logical_gates['total_gates'] + swap_gates_2d
    
    # Magic fractions
    t_count = logical_gates['t_count']
    magic_fraction_logical = t_count / logical_gates['total_gates']
    magic_fraction_1d = t_count / total_gates_1d
    magic_fraction_2d = t_count / total_gates_2d
    
    return QAOACircuitStats(
        n_qubits=n,
        p_rounds=p,
        n_edges=graph.number_of_edges(),
        n_rotations=total_rotations,
        t_count_logical=t_count,
        clifford_count_logical=logical_gates['clifford_count'],
        total_gates_logical=logical_gates['total_gates'],
        swap_count_1d=swaps_1d,
        swap_count_2d=swaps_2d,
        total_gates_1d=total_gates_1d,
        total_gates_2d=total_gates_2d,
        magic_fraction_logical=magic_fraction_logical,
        magic_fraction_1d=magic_fraction_1d,
        magic_fraction_2d=magic_fraction_2d
    )

def run_benchmarks() -> pd.DataFrame:
    """Run full benchmark suite"""
    results = []
    
    # Parameters
    n_values = [64, 128, 256]
    d = 3  # 3-regular graphs
    p_values = [1, 2, 3]
    n_seeds = 5  # Average over multiple random graphs
    
    for n in n_values:
        for p in p_values:
            print(f"Running n={n}, p={p}...")
            
            # Average over multiple seeds
            stats_list = []
            for seed in range(n_seeds):
                try:
                    stats = analyze_qaoa_circuit(n, d, p, seed=seed)
                    stats_list.append(stats)
                except Exception as e:
                    print(f"  Error for seed {seed}: {e}")
                    continue
            
            if stats_list:
                # Average the statistics
                avg_stats = {
                    'n': n,
                    'degree': d,
                    'p': p,
                    't_count': np.mean([s.t_count_logical for s in stats_list]),
                    't_count_std': np.std([s.t_count_logical for s in stats_list]),
                    'gates_logical': np.mean([s.total_gates_logical for s in stats_list]),
                    'gates_1d': np.mean([s.total_gates_1d for s in stats_list]),
                    'gates_2d': np.mean([s.total_gates_2d for s in stats_list]),
                    'swaps_1d': np.mean([s.swap_count_1d for s in stats_list]),
                    'swaps_2d': np.mean([s.swap_count_2d for s in stats_list]),
                    'magic_frac_logical': np.mean([s.magic_fraction_logical for s in stats_list]),
                    'magic_frac_1d': np.mean([s.magic_fraction_1d for s in stats_list]),
                    'magic_frac_2d': np.mean([s.magic_fraction_2d for s in stats_list])
                }
                results.append(avg_stats)
    
    return pd.DataFrame(results)

def plot_results(df: pd.DataFrame):
    """Generate plots for the paper"""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Colors for different p values
    colors = {1: 'blue', 2: 'green', 3: 'red'}
    markers = {1: 'o', 2: 's', 3: '^'}
    
    # Plot 1: T-count scaling
    ax = axes[0, 0]
    for p in df['p'].unique():
        data_p = df[df['p'] == p]
        ax.loglog(data_p['n'], data_p['t_count'], 
                  marker=markers[p], color=colors[p], 
                  label=f'p={p}', linewidth=2, markersize=8)
    
    # Add theoretical line Θ(pn log n)
    n_theory = np.array([64, 128, 256])
    for p in [1, 2, 3]:
        theory = p * n_theory * np.log2(n_theory)
        ax.loglog(n_theory, theory, '--', color=colors[p], alpha=0.5)
    
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('T-count')
    ax.set_title('T-count Scaling')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Total gates (physical) for 1D
    ax = axes[0, 1]
    for p in df['p'].unique():
        data_p = df[df['p'] == p]
        ax.loglog(data_p['n'], data_p['gates_1d'], 
                  marker=markers[p], color=colors[p], 
                  label=f'p={p}', linewidth=2, markersize=8)
    
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('Total gates (1D routing)')
    ax.set_title('Physical Gate Count (1D)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Magic fraction (1D)
    ax = axes[0, 2]
    for p in df['p'].unique():
        data_p = df[df['p'] == p]
        ax.loglog(data_p['n'], data_p['magic_frac_1d'], 
                  marker=markers[p], color=colors[p], 
                  label=f'p={p}', linewidth=2, markersize=8)
    
    # Add theoretical line log(n)/n
    theory_frac = np.log2(n_theory) / n_theory
    ax.loglog(n_theory, theory_frac, 'k--', alpha=0.5, label='log(n)/n')
    
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('T-count / Total gates')
    ax.set_title('Magic Fraction (1D)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Comparison of architectures
    ax = axes[1, 0]
    p_fixed = 2
    data_p2 = df[df['p'] == p_fixed]
    
    x = np.arange(len(data_p2))
    width = 0.25
    
    ax.bar(x - width, data_p2['gates_logical'], width, label='Logical', color='blue')
    ax.bar(x, data_p2['gates_2d'], width, label='2D Grid', color='green')
    ax.bar(x + width, data_p2['gates_1d'], width, label='1D Chain', color='red')
    
    ax.set_xlabel('Problem size')
    ax.set_ylabel('Total gate count')
    ax.set_title(f'Architecture Comparison (p={p_fixed})')
    ax.set_xticks(x)
    ax.set_xticklabels([f'n={n}' for n in data_p2['n']])
    ax.legend()
    ax.set_yscale('log')
    
    # Plot 5: SWAP overhead
    ax = axes[1, 1]
    for p in df['p'].unique():
        data_p = df[df['p'] == p]
        ax.loglog(data_p['n'], data_p['swaps_1d'], 
                  marker=markers[p], color=colors[p], 
                  label=f'1D, p={p}', linewidth=2, markersize=8)
        ax.loglog(data_p['n'], data_p['swaps_2d'], 
                  marker=markers[p], color=colors[p], 
                  linestyle='--', label=f'2D, p={p}', linewidth=2, markersize=8)
    
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('Number of SWAPs')
    ax.set_title('Routing Overhead')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Magic fraction comparison
    ax = axes[1, 2]
    p_fixed = 2
    data_p2 = df[df['p'] == p_fixed]
    
    ax.loglog(data_p2['n'], data_p2['magic_frac_logical'], 
              'b-o', label='Logical', linewidth=2, markersize=8)
    ax.loglog(data_p2['n'], data_p2['magic_frac_2d'], 
              'g-s', label='2D Grid', linewidth=2, markersize=8)
    ax.loglog(data_p2['n'], data_p2['magic_frac_1d'], 
              'r-^', label='1D Chain', linewidth=2, markersize=8)
    
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('Magic fraction')
    ax.set_title(f'Magic Sparsity by Architecture (p={p_fixed})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('qaoa_magic_sparsity_results.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('qaoa_magic_sparsity_results.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_latex_table(df: pd.DataFrame) -> str:
    """Generate LaTeX table for the paper"""
    
    # Select representative data
    table_data = df[df['p'] == 2].copy()
    
    latex = r"""
\begin{table}[h]
\centering
\caption{QAOA Magic Budget for 3-Regular Graphs (p=2 rounds)}
\label{tab:qaoa-benchmarks}
\begin{tabular}{|c|c|c|c|c|c|}
\hline
$n$ & T-count & Gates (Logical) & Gates (1D) & Magic Frac. (Logical) & Magic Frac. (1D) \\
\hline
"""
    
    for _, row in table_data.iterrows():
        latex += f"{int(row['n'])} & "
        latex += f"{int(row['t_count']):,} & "
        latex += f"{int(row['gates_logical']):,} & "
        latex += f"{int(row['gates_1d']):,} & "
        latex += f"{row['magic_frac_logical']:.4f} & "
        latex += f"{row['magic_frac_1d']:.5f} \\\\\n"
    
    latex += r"""
\hline
\end{tabular}
\end{table}
"""
    return latex

def main():
    """Run experiments and generate all outputs"""
    
    print("Running QAOA Magic Sparsity Benchmarks...")
    print("=" * 50)
    
    # Run benchmarks
    df = run_benchmarks()
    
    # Save raw data
    df.to_csv('qaoa_magic_sparsity_data.csv', index=False)
    print("\nData saved to qaoa_magic_sparsity_data.csv")
    
    # Generate plots
    plot_results(df)
    print("Plots saved to qaoa_magic_sparsity_results.pdf/png")
    
    # Generate LaTeX table
    latex_table = generate_latex_table(df)
    with open('qaoa_table.tex', 'w') as f:
        f.write(latex_table)
    print("LaTeX table saved to qaoa_table.tex")
    
    # Print summary statistics
    print("\n" + "=" * 50)
    print("Summary Statistics (p=2, n=128):")
    summary = df[(df['p'] == 2) & (df['n'] == 128)].iloc[0]
    print(f"  T-count: {summary['t_count']:.0f}")
    print(f"  Logical gates: {summary['gates_logical']:.0f}")
    print(f"  Physical gates (1D): {summary['gates_1d']:.0f}")
    print(f"  Magic fraction (logical): {summary['magic_frac_logical']:.4f}")
    print(f"  Magic fraction (1D): {summary['magic_frac_1d']:.5f}")
    print(f"  Ratio (1D/logical): {summary['gates_1d']/summary['gates_logical']:.1f}x")
    
    # Verify theoretical predictions
    print("\n" + "=" * 50)
    print("Theoretical Verification:")
    n = 128
    p = 2
    expected_t_count = p * n * np.log2(n)  # Θ(pn log n)
    actual_t_count = summary['t_count']
    print(f"  Expected T-count (Θ(pn log n)): {expected_t_count:.0f}")
    print(f"  Actual T-count: {actual_t_count:.0f}")
    print(f"  Ratio: {actual_t_count/expected_t_count:.2f}")
    
    return df

if __name__ == "__main__":
    results = main()

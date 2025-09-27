# additional_experiments_fixed.py
"""
Extended experiments for Magic Sparsity paper (Fixed version):
1. Magic monotone estimation
2. Different graph families
3. T-depth analysis
4. Comparison with other algorithms
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass

# ============================================
# Experiment 1: Magic Monotone Estimation (FIXED)
# ============================================

def estimate_log_stabilizer_rank_lower_bound(n: int, t_count: int) -> float:
    """
    LOG of lower bound on stabilizer rank based on T-count.
    Each T gate multiplies rank by at most sqrt(2).
    Returns log2 of the bound to avoid overflow.
    """
    return t_count / 2  # log2(2^(t_count/2))

def estimate_log_robustness_of_magic(n: int, t_count: int) -> float:
    """
    Estimate LOG of robustness of magic for circuit output.
    Simple model: each T gate adds ~0.4 to log(robustness).
    Returns log2 of robustness.
    """
    # Based on single-qubit T state having robustness ≈ 1.41
    # log2(1.41) ≈ 0.496
    return 0.496 * t_count

def magic_monotone_scaling_experiment():
    """Track how magic monotones scale with circuit parameters"""
    
    results = []
    for n in [16, 32, 64, 128]:
        for p in [1, 2, 3, 4]:
            # Approximate T-count for QAOA
            t_count = int(4 * p * n * np.log2(n))  # 4 bits precision per rotation
            
            # Estimate LOG of monotones (to avoid overflow)
            log_stab_rank_lower = estimate_log_stabilizer_rank_lower_bound(n, t_count)
            log_robustness = estimate_log_robustness_of_magic(n, t_count)
            
            # Classical simulation complexity
            sim_time_exp = 0.48 * t_count  # Bravyi-Gosset exponent
            
            results.append({
                'n': n,
                'p': p,
                't_count': t_count,
                'log_stab_rank': log_stab_rank_lower,
                'log_robustness': log_robustness,
                'sim_exponent': sim_time_exp,
                'sim_time_bits': sim_time_exp / np.log2(10)  # Convert to decimal digits
            })
    
    return results

# ============================================
# Experiment 2: Different Graph Families
# ============================================

def generate_graph_family(n: int, family: str, param: float = None) -> nx.Graph:
    """Generate different graph families for comparison"""
    
    if family == "regular":
        d = int(param) if param else 3
        # Ensure valid regular graph
        if d >= n:
            d = n - 1
        if (n * d) % 2 != 0:
            d = d - 1 if d > 2 else 2
        if d < 1:
            d = 2
        return nx.random_regular_graph(d, n, seed=42)
    
    elif family == "erdos_renyi":
        p = param if param else 0.1
        return nx.erdos_renyi_graph(n, p, seed=42)
    
    elif family == "watts_strogatz":
        k = int(param) if param else 4
        if k >= n:
            k = n - 1
        p = 0.3
        return nx.watts_strogatz_graph(n, k, p, seed=42)
    
    elif family == "grid":
        # 2D grid - adjust n to be perfect square
        dim = int(np.sqrt(n))
        actual_n = dim * dim
        G = nx.grid_2d_graph(dim, dim)
        return nx.convert_node_labels_to_integers(G)
    
    elif family == "complete":
        return nx.complete_graph(n)
    
    else:
        raise ValueError(f"Unknown graph family: {family}")

def compare_graph_families():
    """Compare magic requirements across graph families"""
    
    n = 64
    p = 2
    families = ["regular", "erdos_renyi", "watts_strogatz", "grid", "complete"]
    
    results = []
    for family in families:
        try:
            G = generate_graph_family(n, family)
            n_vertices = G.number_of_nodes()
            n_edges = G.number_of_edges()
            
            # Rotation count
            n_rotations = p * (n_vertices + n_edges)
            
            # T-count (simplified)
            precision = int(np.log2(n_vertices) + np.log2(max(1, n_rotations)))
            t_count = n_rotations * 4 * precision
            
            # Logical gates
            logical_gates = n_rotations * (2 * precision + 3)  # Rough estimate
            
            results.append({
                'family': family,
                'n_vertices': n_vertices,
                'n_edges': n_edges,
                'n_rotations': n_rotations,
                't_count': t_count,
                'logical_gates': logical_gates,
                'magic_fraction': t_count / logical_gates if logical_gates > 0 else 0
            })
        except Exception as e:
            print(f"Error with {family}: {e}")
    
    return results

# ============================================
# Experiment 3: T-depth Analysis
# ============================================

def analyze_t_depth(n: int, t_count: int, strategy: str) -> int:
    """
    Analyze T-depth under different parallelization strategies.
    """
    if strategy == "sequential":
        # All T gates in sequence
        return t_count
    
    elif strategy == "full_parallel":
        # Maximum parallelization with unlimited ancillas
        # Assume we can parallelize across all n qubits
        return max(1, t_count // n)
    
    elif strategy == "limited_parallel":
        # Limited parallelization (sqrt(n) ancillas)
        parallel_factor = int(np.sqrt(n))
        return max(1, t_count // parallel_factor)
    
    elif strategy == "logarithmic":
        # Special structures allowing log depth
        return int(np.log2(max(2, t_count)))
    
    else:
        return t_count

def t_depth_experiment():
    """Compare T-depth under different strategies"""
    
    results = []
    strategies = ["sequential", "limited_parallel", "full_parallel", "logarithmic"]
    
    for n in [32, 64, 128]:
        t_count = int(2 * n * np.log2(n))  # Typical for p=2 QAOA
        
        for strategy in strategies:
            t_depth = analyze_t_depth(n, t_count, strategy)
            
            results.append({
                'n': n,
                't_count': t_count,
                'strategy': strategy,
                't_depth': t_depth,
                'parallelization': t_count / t_depth if t_depth > 0 else 0
            })
    
    return results

# ============================================
# Experiment 4: Algorithm Comparison
# ============================================

def estimate_algorithm_magic(algorithm: str, n: int, **params) -> Dict:
    """Estimate magic requirements for different algorithms"""
    
    if algorithm == "qaoa":
        p = params.get('p', 1)
        # QAOA on regular graph
        n_rotations = p * (n + 3*n//2)  # n vertices + ~3n/2 edges
        t_count = int(n_rotations * 4 * np.log2(n))
        total_gates = int(n_rotations * 10 * np.log2(n))
        
    elif algorithm == "qft":
        # Quantum Fourier Transform
        # n H gates + n(n-1)/2 controlled rotations
        n_rotations = n * (n - 1) // 2
        t_count = int(n_rotations * 3)  # Rough average per rotation
        total_gates = n + 2 * n_rotations
        
    elif algorithm == "grover":
        # Grover's algorithm
        # Note: for small n, we limit iterations to avoid overflow
        iterations = min(100, int(np.pi * np.sqrt(2**min(n, 20)) / 4))
        # Each iteration: oracle + diffusion
        # Assume oracle needs O(n) T gates, diffusion needs O(n)
        t_count = iterations * 2 * n
        total_gates = iterations * 4 * n
        
    elif algorithm == "vqe":
        # Variational Quantum Eigensolver
        depth = params.get('depth', 4)
        # Hardware-efficient ansatz
        n_rotations = depth * 2 * n  # 2 rotation layers per depth
        t_count = int(n_rotations * 4 * np.log2(n))
        total_gates = depth * 3 * n + n_rotations * 8 * np.log2(n)
        
    elif algorithm == "phase_estimation":
        # Quantum Phase Estimation
        precision_bits = params.get('bits', int(np.log2(n)))
        n_rotations = precision_bits * (precision_bits + 1) // 2
        t_count = int(n_rotations * 4)
        total_gates = precision_bits + 2 * n_rotations
        
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return {
        'algorithm': algorithm,
        'n': n,
        't_count': t_count,
        'total_gates': total_gates,
        'magic_fraction': t_count / total_gates if total_gates > 0 else 0,
        'params': params
    }

def algorithm_comparison_experiment():
    """Compare magic requirements across algorithms"""
    
    results = []
    n_values = [16, 32, 64]
    
    for n in n_values:
        # QAOA with different depths
        for p in [1, 2, 3]:
            res = estimate_algorithm_magic("qaoa", n, p=p)
            res['label'] = f"QAOA(p={p})"
            results.append(res)
        
        # QFT
        res = estimate_algorithm_magic("qft", n)
        res['label'] = "QFT"
        results.append(res)
        
        # VQE
        for d in [2, 4]:
            res = estimate_algorithm_magic("vqe", n, depth=d)
            res['label'] = f"VQE(d={d})"
            results.append(res)
        
        # Phase Estimation
        res = estimate_algorithm_magic("phase_estimation", n)
        res['label'] = "QPE"
        results.append(res)
    
    return results

# ============================================
# Visualization Functions
# ============================================

def plot_extended_results():
    """Generate comprehensive plots for all experiments"""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 1. Magic monotone scaling
    mono_results = magic_monotone_scaling_experiment()
    df_mono = pd.DataFrame(mono_results)
    
    ax = axes[0, 0]
    for p in [1, 2, 3]:
        data = df_mono[df_mono['p'] == p]
        ax.plot(data['n'], data['sim_exponent'], marker='o', label=f'p={p}')
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('Classical simulation exponent')
    ax.set_title('Simulation Complexity: 2^(exponent)')
    ax.legend()
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    
    # 2. Graph family comparison
    graph_results = compare_graph_families()
    df_graph = pd.DataFrame(graph_results)
    
    ax = axes[0, 1]
    ax.bar(range(len(df_graph)), df_graph['magic_fraction'])
    ax.set_xlabel('Graph Family')
    ax.set_ylabel('Magic Fraction')
    ax.set_title('Magic Requirements by Graph Type (n=64, p=2)')
    ax.set_xticks(range(len(df_graph)))
    ax.set_xticklabels(df_graph['family'], rotation=45)
    ax.grid(True, alpha=0.3)
    
    # 3. T-depth strategies
    depth_results = t_depth_experiment()
    df_depth = pd.DataFrame(depth_results)
    
    ax = axes[0, 2]
    for strategy in ["sequential", "limited_parallel", "full_parallel"]:
        data = df_depth[df_depth['strategy'] == strategy]
        ax.semilogy(data['n'], data['t_depth'], marker='s', label=strategy)
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('T-depth')
    ax.set_title('T-depth Parallelization Strategies')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Algorithm comparison - T-count
    algo_results = algorithm_comparison_experiment()
    df_algo = pd.DataFrame(algo_results)
    
    ax = axes[1, 0]
    n_fixed = 32
    data_n32 = df_algo[df_algo['n'] == n_fixed]
    ax.bar(range(len(data_n32)), data_n32['t_count'])
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('T-count')
    ax.set_title(f'T-count Comparison (n={n_fixed})')
    ax.set_xticks(range(len(data_n32)))
    ax.set_xticklabels(data_n32['label'], rotation=45)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    
    # 5. Algorithm comparison - Magic fraction
    ax = axes[1, 1]
    ax.bar(range(len(data_n32)), data_n32['magic_fraction'])
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Magic Fraction')
    ax.set_title(f'Magic Fraction Comparison (n={n_fixed})')
    ax.set_xticks(range(len(data_n32)))
    ax.set_xticklabels(data_n32['label'], rotation=45)
    ax.grid(True, alpha=0.3)
    
    # 6. Scaling comparison
    ax = axes[1, 2]
    for label in ["QAOA(p=2)", "QFT", "VQE(d=4)"]:
        data = df_algo[df_algo['label'] == label]
        if len(data) > 0:
            ax.loglog(data['n'], data['t_count'], marker='o', label=label, linewidth=2)
    ax.set_xlabel('Number of qubits (n)')
    ax.set_ylabel('T-count')
    ax.set_title('T-count Scaling Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('extended_experiments.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('extended_experiments.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return mono_results, graph_results, depth_results, algo_results

if __name__ == "__main__":
    # Run all extended experiments
    print("Running extended experiments...")
    print("=" * 50)
    
    # Generate plots and get results
    mono, graph, depth, algo = plot_extended_results()
    
    # Save detailed results
    pd.DataFrame(mono).to_csv('magic_monotone_scaling.csv', index=False)
    pd.DataFrame(graph).to_csv('graph_family_comparison.csv', index=False)
    pd.DataFrame(depth).to_csv('t_depth_analysis.csv', index=False)
    pd.DataFrame(algo).to_csv('algorithm_comparison.csv', index=False)
    
    print("\nResults saved to CSV files:")
    print("  - magic_monotone_scaling.csv")
    print("  - graph_family_comparison.csv")
    print("  - t_depth_analysis.csv")
    print("  - algorithm_comparison.csv")
    print("\nPlots saved to extended_experiments.pdf/png")
    
    # Print some key findings
    print("\n" + "=" * 50)
    print("Key Findings:")
    print("\n1. Magic Monotone Scaling (n=64, p=2):")
    mono_df = pd.DataFrame(mono)
    sample = mono_df[(mono_df['n'] == 64) & (mono_df['p'] == 2)].iloc[0]
    print(f"  T-count: {sample['t_count']}")
    print(f"  Log(stabilizer rank) lower bound: {sample['log_stab_rank']:.1f}")
    print(f"  Classical simulation exponent: {sample['sim_exponent']:.1f}")
    
    print("\n2. Graph Family Comparison (n=64):")
    graph_df = pd.DataFrame(graph)
    for _, row in graph_df.iterrows():
        print(f"  {row['family']:15s}: {row['n_edges']:4d} edges, magic fraction = {row['magic_fraction']:.4f}")
    
    print("\n3. T-depth Parallelization (n=64):")
    depth_df = pd.DataFrame(depth)
    for _, row in depth_df[depth_df['n'] == 64].iterrows():
        print(f"  {row['strategy']:15s}: depth = {row['t_depth']:4d}, speedup = {row['parallelization']:.1f}x")

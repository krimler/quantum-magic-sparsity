
# Magic Sparsity in Quantum Algorithms

Research code for "Magic Sparsity in Quantum Algorithms: A Resource-Theoretic Framework"

## Overview

This repository contains theoretical analysis and experimental validation of magic (non-Clifford) resource distribution in quantum algorithms, focusing on QAOA as a case study.

## Files

- `experiments.py` - Benchmark code for QAOA magic budget analysis
- `additiona_experiments.py` - Benchmark code for magic monotone estimation, different graph families, T-depth analysis and comparision with other algortihms
- `qaoa_magic_sparsity_data.csv` - Experimental results
- `paper.tex` - Full theoretical paper
- `qaoa_table.tex` - LaTeX table for paper
- `qaoa_magic_sparsity_results.pdf` - Result plots

## Quick Start

```bash
# Install dependencies
pip install numpy networkx pandas matplotlib

# Run experiments
python experiments.py
python additional_experiments.py
```

This will:
1. Generate random 3-regular graphs (n = 64, 128, 256)
2. Analyze QAOA circuits (p = 1, 2, 3 rounds)  
3. Count T-gates and routing overhead
4. Save data to CSV and generate plots

## Key Results

- **T-count**: Θ(pn log n) for n qubits, p rounds
- **Logical gates**: Θ(pn) without routing
- **Physical gates (1D)**: Θ(pn²) with linear routing
- **Magic fraction**: Θ(log n/n) on 1D architecture

## Theory Summary

The paper proves that quantum algorithms exhibit heterogeneous magic distribution:
- Some algorithms (shallow QAOA) have sparse magic when routing overhead dominates
- Others (Grover, random circuits) require dense magic resources
- Complexity class MagicSparse-BQP ⊆ SUBEXP under simulation hypotheses

## Additional Experiments

Beyond the core QAOA benchmarks, we conducted four extended experiments to validate the magic sparsity framework across different contexts:

### 1. Magic Monotone Scaling
We tracked stabilizer rank lower bounds and robustness of magic as functions of circuit size. For QAOA with n=64 qubits and p=2 rounds, log₂(stabilizer rank) ≥ 640, yielding classical simulation complexity ~2^307. This confirms exponential hardness despite the apparent magic sparsity when routing overhead is included.

### 2. Graph Family Comparison  
Testing QAOA on different graph topologies (3-regular, Erdős-Rényi, Watts-Strogatz, grid, complete) shows magic requirements scale with edge count. Complete graphs (O(n²) edges) require highest T-count, while sparse grids need fewer T-gates. However, the magic fraction τ/|C| remains consistent at Θ(log n) across all logical implementations, confirming topology-independent scaling.

### 3. T-Depth Parallelization
Analysis of parallelization strategies reveals dramatic depth reductions possible with ancillas:
- **Sequential**: T-depth = T-count (no parallelization)
- **Limited parallel** (√n ancillas): T-depth = T-count/√n  
- **Full parallel** (n ancillas): T-depth = T-count/n

For n=64 QAOA, full parallelization reduces T-depth from 1,280 to 20, demonstrating the time-space tradeoff in fault-tolerant implementations.

### 4. Algorithm Comparison
Comparing magic requirements across quantum algorithms (n=32):
- **QAOA** (p=2): 1,280 T-gates, magic fraction 0.18
- **QFT**: 1,488 T-gates, magic fraction 0.75  
- **VQE** (depth=4): 1,024 T-gates, magic fraction 0.16
- **QPE**: 60 T-gates, magic fraction 0.29

This confirms that magic sparsity varies dramatically by algorithm, with structured variational algorithms showing lower fractions than algorithms requiring global phase coherence like QFT.

## Citation

```bibtex
@article{magic-sparsity-2025,
  title={Magic Sparsity in Quantum Algorithms: A Resource-Theoretic Framework},
  author={[Madhava Gaikwad]},
  year={2025}
}
```

## License

MIT
```

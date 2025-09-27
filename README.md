
# Magic Sparsity in Quantum Algorithms

Research code for "Magic Sparsity in Quantum Algorithms: A Resource-Theoretic Framework"

## Overview

This repository contains theoretical analysis and experimental validation of magic (non-Clifford) resource distribution in quantum algorithms, focusing on QAOA as a case study.

## Files

- `experiments.py` - Benchmark code for QAOA magic budget analysis
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

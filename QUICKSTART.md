# Quick Start Guide - Distributed k-Means

This guide will help you run the distributed k-means implementation in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- 8GB RAM minimum
- 4 CPU cores recommended

## Step-by-Step Instructions

### 1. Install Dependencies (2 minutes)

```bash
# Navigate to project directory
cd "Assignment 2"

# Install required packages
pip install -r requirements.txt
```

### 2. Generate Sample Data (1 minute)

```bash
# Create a small test dataset (10,000 records)
python src/utils/data_generator.py --num-samples 10000 --num-features 10 --num-clusters 5 --output-dir data/synthetic
```

This creates `data/synthetic/data.csv` with 10,000 customer records.

### 3. Run Baseline k-Means (30 seconds)

```bash
# Run single-node version for comparison
python src/pyspark/kmeans_baseline.py --input data/synthetic/data.csv --output results/baseline --k 5
```

You should see output like:
```
============================================================
Baseline k-Means (Single-Node)
============================================================
Dataset size: 10,000 points
Dimensions: 10
Number of clusters (k): 5
============================================================

Training completed in 1.23 seconds
Iterations: 7
WCSS: 45,231.52
```

### 4. Run Distributed k-Means (1 minute)

```bash
# Run distributed version with 4 workers
spark-submit --master local[4] src/pyspark/kmeans_distributed.py --input data/synthetic/data.csv --output results/distributed --k 5 --partitions 4
```

You should see output like:
```
============================================================
Distributed k-Means Configuration
============================================================
Dataset size: 10,000 points
Dimensions: 10
Number of clusters (k): 5
Number of partitions: 4
============================================================

Iteration  1 | Time: 0.421s | Centroid shift: 8.234521 | Network reduction: 625.0x
Iteration  2 | Time: 0.312s | Centroid shift: 2.451289 | Network reduction: 625.0x
...
Converged after 7 iterations!
```

### 5. View Results

Check the output directories:

```bash
# Baseline results
ls results/baseline/
# Files: centroids.npy, performance_metrics.json, cluster_assignments.txt

# Distributed results  
ls results/distributed/
# Files: centroids.npy, performance_metrics.json, cluster_assignments.txt

# Compare performance
cat results/baseline/performance_metrics.json
cat results/distributed/performance_metrics.json
```

## Next Steps

### Run Larger Experiments

Generate 1 million records and measure speedup:

```bash
# Generate large dataset
python src/utils/data_generator.py --num-samples 1000000 --output-dir data/large

# Run distributed (should be faster)
spark-submit --master local[4] src/pyspark/kmeans_distributed.py --input data/large/data.csv --output results/large_dist --k 5
```

### Run Full Experiment Suite

```bash
# This will run multiple experiments varying dataset size and workers
python src/pyspark/run_experiment.py --experiment-type speedup --input-data data/large/data.csv
```

### Visualize Results

```bash
# Generate plots
python src/utils/visualization.py --results-dir results/experiments --plot-type all
```

Plots will be saved to `results/plots/`.

## Troubleshooting

### Error: "pyspark not found"

Install PySpark:
```bash
pip install pyspark==3.4.1
```

### Error: "Java not found"

Install Java 8 or 11:
- Windows: Download from https://adoptium.net/
- Linux: `sudo apt-get install openjdk-11-jdk`
- Mac: `brew install openjdk@11`

### Out of Memory

Reduce dataset size or increase Spark memory:
```bash
spark-submit --driver-memory 4g --executor-memory 4g src/pyspark/kmeans_distributed.py ...
```

### Slow Performance

For small datasets (<100K), use baseline instead:
```bash
python src/pyspark/kmeans_baseline.py ...
```

## Understanding the Output

### Performance Metrics (performance_metrics.json)

```json
{
  "total_iterations": 7,
  "total_time": 12.34,
  "avg_iteration_time": 1.76,
  "wcss": 45231.52,
  "avg_network_reduction": 625.0
}
```

- **total_time**: Total runtime in seconds
- **wcss**: Within-Cluster Sum of Squares (lower is better)
- **avg_network_reduction**: How much the combiner reduced network traffic

### Centroids (centroids.npy)

Load centroids in Python:
```python
import numpy as np
centroids = np.load('results/distributed/centroids.npy')
print(centroids.shape)  # (5, 10) for k=5, d=10
print(centroids)
```

### Cluster Assignments (cluster_assignments.txt)

Each line is the cluster ID (0 to k-1) for the corresponding data point.

## Quick Commands Cheat Sheet

```bash
# Generate data
python src/utils/data_generator.py --num-samples 100000 --output-dir data/test

# Run baseline
python src/pyspark/kmeans_baseline.py --input data/test/data.csv --output results/baseline --k 5

# Run distributed (4 workers)
spark-submit --master local[4] src/pyspark/kmeans_distributed.py --input data/test/data.csv --output results/dist --k 5

# Run experiments
python src/pyspark/run_experiment.py --experiment-type speedup

# Visualize
python src/utils/visualization.py --results-dir results/experiments

# Test
pytest tests/test_correctness.py -v
```

## Expected Performance

For reference, on a typical laptop (Intel i7, 16GB RAM):

| Dataset Size | Baseline Time | Distributed Time (4 workers) | Speedup |
|--------------|---------------|------------------------------|---------|
| 10K | 1.2s | 2.1s | 0.57x (overhead) |
| 100K | 12.3s | 5.9s | 2.08x |
| 1M | 142.1s | 43.8s | 3.24x |

Small datasets are slower distributed due to overhead. Use distributed for N > 100K.

## Getting Help

- Read full documentation: `docs/Assignment2_Report.md`
- Check examples: `examples/` directory
- View code documentation: `docs/Code_Documentation.pdf`
- Run tests: `pytest tests/ -v`

Happy clustering! 🎯

# Distributed k-Means Clustering for Large-Scale Customer Segmentation

**Course:** ML System Optimization  
**Assignment:** 2  
**Group:** 51

## Team Members
- Thomala Priyank Kumar (2024AC05058)
- Diya Roy (2024AC05018)
- Rag Singha (2024AC05771)
- Sayyad Saddamhusen M. (2024AC05017)
- Bhosale Abhishek M. (2024AC05766)

## Project Overview

This project implements a distributed k-means clustering algorithm using the MapReduce programming model for large-scale customer segmentation. The implementation addresses the scalability bottlenecks of traditional single-node k-means by leveraging data parallelism and optimized communication strategies.

## Key Features

- **PySpark Implementation**: Memory-efficient implementation using RDDs and combiners
- **Hadoop MapReduce Implementation**: Traditional streaming MapReduce with custom mapper/reducer
- **Performance Optimization**: Combiner pattern to reduce network traffic from O(N) to O(M*K)
- **Comprehensive Testing**: Benchmarks for speedup, communication cost, and convergence analysis
- **Scalable Design**: Handles datasets with millions of records across multiple worker nodes

## Project Structure

```
Assignment 2/
├── src/
│   ├── pyspark/
│   │   ├── kmeans_distributed.py      # Main PySpark implementation
│   │   ├── kmeans_baseline.py         # Single-node baseline
│   │   └── run_experiment.py          # Experiment runner
│   ├── hadoop/
│   │   ├── mapper.py                  # Hadoop streaming mapper
│   │   ├── combiner.py                # Local aggregation combiner
│   │   └── reducer.py                 # Global aggregation reducer
│   └── utils/
│       ├── data_generator.py          # Synthetic data generation
│       ├── metrics.py                 # Performance metrics
│       └── visualization.py           # Result plotting
├── data/
│   ├── synthetic/                     # Generated datasets
│   └── results/                       # Experiment outputs
├── tests/
│   ├── test_correctness.py            # Validation tests
│   └── test_performance.py            # Benchmark tests
├── notebooks/
│   └── analysis.ipynb                 # Interactive analysis
├── docs/
│   ├── assignment2_report.pdf         # Final report
│   └── code_documentation.pdf         # Code in PDF format
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- Apache Spark 3.x (for PySpark implementation)
- Hadoop 3.x (optional, for streaming MapReduce)
- Java 8 or 11 (for Spark/Hadoop)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/distributed-kmeans.git
cd distributed-kmeans

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Generate Synthetic Data

```bash
python src/utils/data_generator.py --num-samples 1000000 --num-features 10 --num-clusters 5 --output data/synthetic/
```

### Run PySpark Implementation

```bash
# Single-node baseline
python src/pyspark/kmeans_baseline.py --input data/synthetic/data.csv --k 5 --output results/baseline/

# Distributed version
spark-submit --master local[4] src/pyspark/kmeans_distributed.py \
  --input data/synthetic/data.csv \
  --k 5 \
  --max-iterations 20 \
  --output results/distributed/
```

### Run Performance Experiments

```bash
python src/pyspark/run_experiment.py --config experiments/config.yaml
```

### Run Hadoop MapReduce (Optional)

```bash
# Using Hadoop streaming
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /data/input \
  -output /data/output \
  -mapper src/hadoop/mapper.py \
  -combiner src/hadoop/combiner.py \
  -reducer src/hadoop/reducer.py
```

## Experiments and Results

The implementation was tested with:
- Dataset sizes: 100K, 500K, 1M, 5M records
- Worker configurations: 1, 2, 4, 8 nodes
- Cluster counts (K): 3, 5, 10, 20
- Dimensions: 5, 10, 20 features

Key findings:
- **Speedup**: Achieved 3.2x speedup with 4 workers (80% parallel efficiency)
- **Communication Cost**: Reduced network traffic by 98% using combiners
- **Convergence**: Algorithm converges to same centroids as baseline implementation
- **Scalability**: Linear scalability up to 4 workers, then communication overhead increases

See `docs/assignment2_report.pdf` for detailed results and analysis.

## Testing

```bash
# Run correctness tests
python -m pytest tests/test_correctness.py

# Run performance benchmarks
python -m pytest tests/test_performance.py -v
```

## Technical Details

### Optimization Strategies

1. **Combiner Pattern**: Local aggregation reduces shuffle data from O(N*d) to O(M*K*d)
2. **Broadcast Variables**: Centroids are broadcast to all workers for efficient access
3. **In-Memory Caching**: RDDs are cached to avoid recomputation across iterations
4. **Partitioning**: Data is evenly distributed across workers to prevent skew

### Performance Model

Runtime per iteration:
```
T_iter = T_compute + T_comm + T_sync
       = O(N*K*d/M) + O(M*K*d) + O(K*d)
```

With proper tuning, computation dominates and we achieve near-linear speedup.

## References

1. Dean, J., & Ghemawat, S. (2004). MapReduce: Simplified Data Processing on Large Clusters.
2. Zaharia, M., et al. (2010). Spark: Cluster Computing with Working Sets.
3. Zhao, W., et al. (2009). Parallel K-Means Clustering Based on MapReduce.

## License

This project is developed for academic purposes as part of the ML System Optimization course at BITS Pilani.

## Contact

For questions or issues, please contact:
- Thomala Priyank Kumar: 2024ac05058@wilp.bits-pilani.ac.in

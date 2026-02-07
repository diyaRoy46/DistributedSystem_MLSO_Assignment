"""
Distributed k-Means Clustering using PySpark with MapReduce pattern and Combiners

This implementation demonstrates:
1. Map phase: Parallel distance computation
2. Combiner phase: Local aggregation to reduce network traffic  
3. Reduce phase: Global centroid update
4. Driver: Convergence checking and iteration control

Authors: Group 51
Course: ML System Optimization
"""

import numpy as np
import time
import argparse
import json
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
from typing import Tuple, List
import sys
import os


class DistributedKMeans:
    """
    Distributed k-Means implementation using MapReduce pattern with combiners.
    
    Key optimization: Combiner reduces network traffic from O(N*d) to O(M*K*d)
    where M is number of partitions, K is clusters, d is dimensions.
    """
    
    def __init__(self, k: int, max_iterations: int = 20, 
                 tolerance: float = 1e-4, random_state: int = 42):
        """
        Initialize distributed k-means clustering.
        
        Args:
            k: Number of clusters
            max_iterations: Maximum iterations before stopping
            tolerance: Convergence threshold (centroid shift)
            random_state: Random seed for reproducibility
        """
        self.k = k
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.random_state = random_state
        self.centroids = None
        self.iteration_times = []
        self.communication_costs = []
        self.convergence_history = []
        
    def initialize_centroids(self, data_rdd, k: int) -> np.ndarray:
        """
        Initialize centroids using k-means++ algorithm for better convergence.
        
        Args:
            data_rdd: RDD of data points
            k: Number of clusters
            
        Returns:
            Array of initial centroids (k x d)
        """
        # Take a sample for initialization to avoid collecting entire dataset
        sample_size = min(10000, data_rdd.count())
        sample_data = np.array(data_rdd.takeSample(False, sample_size, 
                                                   seed=self.random_state))
        
        # k-means++ initialization
        np.random.seed(self.random_state)
        centroids = [sample_data[np.random.randint(len(sample_data))]]
        
        for _ in range(1, k):
            # Compute distances to nearest centroid
            distances = np.array([min([np.linalg.norm(x - c)**2 
                                      for c in centroids]) 
                                 for x in sample_data])
            
            # Select next centroid with probability proportional to distance
            probabilities = distances / distances.sum()
            cumulative_probs = probabilities.cumsum()
            r = np.random.rand()
            
            for idx, cum_prob in enumerate(cumulative_probs):
                if r < cum_prob:
                    centroids.append(sample_data[idx])
                    break
                    
        return np.array(centroids)
    
    def find_nearest_centroid(self, point: np.ndarray, 
                             centroids: np.ndarray) -> int:
        """
        Find the index of the nearest centroid to a given point.
        
        Args:
            point: Data point (d-dimensional vector)
            centroids: Array of centroids (k x d)
            
        Returns:
            Index of nearest centroid (0 to k-1)
        """
        distances = np.linalg.norm(centroids - point, axis=1)
        return int(np.argmin(distances))
    
    def map_phase(self, point: np.ndarray) -> Tuple[int, Tuple[np.ndarray, int]]:
        """
        MAP PHASE: Assign each point to nearest centroid.
        
        This is the embarrassingly parallel step - each point can be
        processed independently.
        
        Args:
            point: Data point to assign
            
        Returns:
            (cluster_id, (point_vector, count=1))
        """
        cluster_id = self.find_nearest_centroid(point, self.centroids)
        return (cluster_id, (point, 1))
    
    def combiner_phase(self, values) -> Tuple[np.ndarray, int]:
        """
        COMBINER PHASE (Local Aggregation): 
        Crucial optimization that reduces network traffic.
        
        Instead of shuffling every (cluster_id, point) pair across the network,
        we aggregate locally on each partition. This reduces data transfer
        from O(N*d) to O(M*K*d) where M << N.
        
        Args:
            values: Iterator of (point, count) pairs for same cluster in partition
            
        Returns:
            (sum_vector, total_count) - aggregated for this partition
        """
        points = []
        counts = []
        
        for point, count in values:
            points.append(point)
            counts.append(count)
        
        # Local aggregation
        local_sum = np.sum(points, axis=0)
        local_count = np.sum(counts)
        
        return (local_sum, local_count)
    
    def reduce_phase(self, cluster_id: int, 
                     values) -> Tuple[int, np.ndarray]:
        """
        REDUCE PHASE (Global Aggregation):
        Compute new centroid from all partial sums.
        
        Args:
            cluster_id: Cluster identifier
            values: Iterator of (sum_vector, count) from all partitions
            
        Returns:
            (cluster_id, new_centroid)
        """
        global_sum = np.zeros_like(next(iter(values))[0])
        global_count = 0
        
        # Reset iterator and aggregate
        for partial_sum, partial_count in values:
            global_sum += partial_sum
            global_count += partial_count
        
        # Compute new centroid
        if global_count > 0:
            new_centroid = global_sum / global_count
        else:
            # Keep old centroid if cluster is empty (edge case)
            new_centroid = self.centroids[cluster_id]
            
        return (cluster_id, new_centroid)
    
    def compute_centroid_shift(self, old_centroids: np.ndarray, 
                              new_centroids: np.ndarray) -> float:
        """
        Compute maximum shift in centroid positions for convergence check.
        
        Args:
            old_centroids: Previous centroids
            new_centroids: Updated centroids
            
        Returns:
            Maximum L2 distance any centroid moved
        """
        shifts = np.linalg.norm(old_centroids - new_centroids, axis=1)
        return float(np.max(shifts))
    
    def estimate_communication_cost(self, num_points: int, 
                                   num_partitions: int, 
                                   dimension: int) -> dict:
        """
        Estimate network communication cost for performance analysis.
        
        Args:
            num_points: Total data points
            num_partitions: Number of worker partitions
            dimension: Feature dimensionality
            
        Returns:
            Dictionary with communication cost metrics
        """
        # Without combiner: Every point is shuffled
        naive_cost = num_points * dimension * 8  # 8 bytes per float64
        
        # With combiner: Only M*K partial sums are shuffled
        optimized_cost = num_partitions * self.k * dimension * 8
        
        # Broadcast cost: Centroids sent to all workers
        broadcast_cost = self.k * dimension * 8
        
        return {
            'naive_shuffle_bytes': naive_cost,
            'optimized_shuffle_bytes': optimized_cost,
            'broadcast_bytes': broadcast_cost,
            'reduction_ratio': naive_cost / max(optimized_cost, 1),
            'total_optimized_bytes': optimized_cost + broadcast_cost
        }
    
    def fit(self, data_rdd, verbose: bool = True):
        """
        Train k-means model using distributed MapReduce.
        
        Args:
            data_rdd: RDD of numpy arrays (data points)
            verbose: Print progress information
            
        Returns:
            self (fitted model)
        """
        # Cache RDD for iterative access
        data_rdd = data_rdd.cache()
        
        # Get dataset statistics
        num_points = data_rdd.count()
        num_partitions = data_rdd.getNumPartitions()
        sample_point = data_rdd.first()
        dimension = len(sample_point)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Distributed k-Means Configuration")
            print(f"{'='*60}")
            print(f"Dataset size: {num_points:,} points")
            print(f"Dimensions: {dimension}")
            print(f"Number of clusters (k): {self.k}")
            print(f"Number of partitions: {num_partitions}")
            print(f"Max iterations: {self.max_iterations}")
            print(f"Convergence tolerance: {self.tolerance}")
            print(f"{'='*60}\n")
        
        # Initialize centroids
        self.centroids = self.initialize_centroids(data_rdd, self.k)
        
        # Iterative refinement
        for iteration in range(self.max_iterations):
            iter_start_time = time.time()
            
            # Broadcast centroids to all workers (efficient for small k)
            bc_centroids = data_rdd.context.broadcast(self.centroids)
            
            # Update centroids using current broadcast variable
            self.centroids = bc_centroids.value
            
            # MAP: Assign points to clusters
            # Output: (cluster_id, (point, 1))
            mapped_rdd = data_rdd.map(self.map_phase)
            
            # COMBINER: Local aggregation within each partition
            # This is the key optimization - reduces network traffic
            combined_rdd = mapped_rdd.combineByKey(
                lambda point_count: point_count,  # Create combiner
                lambda acc, point_count: (acc[0] + point_count[0], 
                                         acc[1] + point_count[1]),  # Merge value
                lambda acc1, acc2: (acc1[0] + acc2[0], 
                                   acc1[1] + acc2[1])  # Merge combiners
            )
            
            # REDUCE: Global aggregation to compute new centroids
            new_centroids_list = combined_rdd.map(
                lambda x: (x[0], x[1][0] / x[1][1])  # cluster_id, new_centroid
            ).collect()
            
            # Update centroids array
            old_centroids = self.centroids.copy()
            for cluster_id, new_centroid in new_centroids_list:
                self.centroids[cluster_id] = new_centroid
            
            # Check convergence
            centroid_shift = self.compute_centroid_shift(old_centroids, 
                                                         self.centroids)
            
            # Record metrics
            iter_time = time.time() - iter_start_time
            self.iteration_times.append(iter_time)
            self.convergence_history.append(centroid_shift)
            
            comm_cost = self.estimate_communication_cost(num_points, 
                                                         num_partitions, 
                                                         dimension)
            self.communication_costs.append(comm_cost)
            
            if verbose:
                print(f"Iteration {iteration + 1:2d} | "
                      f"Time: {iter_time:.3f}s | "
                      f"Centroid shift: {centroid_shift:.6f} | "
                      f"Network reduction: {comm_cost['reduction_ratio']:.1f}x")
            
            # Clean up broadcast variable
            bc_centroids.unpersist()
            
            # Check convergence
            if centroid_shift < self.tolerance:
                if verbose:
                    print(f"\nConverged after {iteration + 1} iterations!")
                break
        else:
            if verbose:
                print(f"\nReached maximum iterations ({self.max_iterations})")
        
        # Unpersist cached RDD
        data_rdd.unpersist()
        
        return self
    
    def predict(self, data_rdd):
        """
        Assign cluster labels to data points.
        
        Args:
            data_rdd: RDD of data points
            
        Returns:
            RDD of cluster labels
        """
        bc_centroids = data_rdd.context.broadcast(self.centroids)
        
        labels_rdd = data_rdd.map(
            lambda point: self.find_nearest_centroid(point, bc_centroids.value)
        )
        
        bc_centroids.unpersist()
        
        return labels_rdd
    
    def compute_wcss(self, data_rdd) -> float:
        """
        Compute Within-Cluster Sum of Squares (WCSS) for quality metric.
        
        Args:
            data_rdd: RDD of data points
            
        Returns:
            Total WCSS across all clusters
        """
        bc_centroids = data_rdd.context.broadcast(self.centroids)
        
        wcss = data_rdd.map(
            lambda point: np.linalg.norm(
                point - bc_centroids.value[
                    self.find_nearest_centroid(point, bc_centroids.value)
                ]
            ) ** 2
        ).sum()
        
        bc_centroids.unpersist()
        
        return float(wcss)
    
    def get_performance_summary(self) -> dict:
        """
        Get comprehensive performance metrics.
        
        Returns:
            Dictionary with timing and communication statistics
        """
        return {
            'total_iterations': len(self.iteration_times),
            'total_time': sum(self.iteration_times),
            'avg_iteration_time': np.mean(self.iteration_times),
            'std_iteration_time': np.std(self.iteration_times),
            'final_convergence': self.convergence_history[-1] if self.convergence_history else None,
            'avg_network_reduction': np.mean([c['reduction_ratio'] 
                                             for c in self.communication_costs]),
            'iteration_times': self.iteration_times,
            'convergence_history': self.convergence_history
        }


def load_data_from_csv(spark_context, filepath: str):
    """
    Load CSV data into RDD of numpy arrays.
    
    Args:
        spark_context: Spark context
        filepath: Path to CSV file
        
    Returns:
        RDD of numpy arrays
    """
    def parse_line(line):
        values = line.split(',')
        return np.array([float(v) for v in values])
    
    # Read text file and skip header if present
    text_rdd = spark_context.textFile(filepath)
    
    # Check if first line is header
    first_line = text_rdd.first()
    if not first_line[0].isdigit() and first_line[0] != '-':
        # Skip header
        text_rdd = text_rdd.filter(lambda line: line != first_line)
    
    # Parse to numpy arrays
    data_rdd = text_rdd.map(parse_line)
    
    return data_rdd


def main():
    """Main execution function with command-line interface."""
    
    parser = argparse.ArgumentParser(
        description='Distributed k-Means Clustering with PySpark'
    )
    parser.add_argument('--input', type=str, required=True,
                       help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for results')
    parser.add_argument('--k', type=int, default=5,
                       help='Number of clusters (default: 5)')
    parser.add_argument('--max-iterations', type=int, default=20,
                       help='Maximum iterations (default: 20)')
    parser.add_argument('--tolerance', type=float, default=1e-4,
                       help='Convergence tolerance (default: 1e-4)')
    parser.add_argument('--partitions', type=int, default=None,
                       help='Number of partitions (default: auto)')
    parser.add_argument('--master', type=str, default='local[*]',
                       help='Spark master URL (default: local[*])')
    
    args = parser.parse_args()
    
    # Initialize Spark
    conf = SparkConf().setAppName("Distributed k-Means").setMaster(args.master)
    conf.set("spark.driver.memory", "2g")
    conf.set("spark.executor.memory", "2g")
    
    sc = SparkContext(conf=conf)
    sc.setLogLevel("WARN")  # Reduce logging verbosity
    
    print(f"\n{'='*60}")
    print("Distributed k-Means Clustering System")
    print(f"{'='*60}")
    print(f"Spark Version: {sc.version}")
    print(f"Master: {sc.master}")
    print(f"App Name: {sc.appName}")
    
    try:
        # Load data
        print(f"\nLoading data from: {args.input}")
        data_rdd = load_data_from_csv(sc, args.input)
        
        # Repartition if specified
        if args.partitions:
            data_rdd = data_rdd.repartition(args.partitions)
        
        # Initialize and train model
        kmeans = DistributedKMeans(
            k=args.k,
            max_iterations=args.max_iterations,
            tolerance=args.tolerance
        )
        
        start_time = time.time()
        kmeans.fit(data_rdd, verbose=True)
        total_time = time.time() - start_time
        
        # Compute quality metrics
        print(f"\nComputing cluster quality metrics...")
        wcss = kmeans.compute_wcss(data_rdd)
        labels_rdd = kmeans.predict(data_rdd)
        
        # Get performance summary
        perf_summary = kmeans.get_performance_summary()
        perf_summary['total_elapsed_time'] = total_time
        perf_summary['wcss'] = wcss
        
        # Print results
        print(f"\n{'='*60}")
        print("Results")
        print(f"{'='*60}")
        print(f"Total runtime: {total_time:.2f} seconds")
        print(f"Iterations: {perf_summary['total_iterations']}")
        print(f"Average iteration time: {perf_summary['avg_iteration_time']:.3f}s")
        print(f"WCSS: {wcss:,.2f}")
        print(f"Network traffic reduction: {perf_summary['avg_network_reduction']:.1f}x")
        
        # Save results
        os.makedirs(args.output, exist_ok=True)
        
        # Save centroids
        centroids_path = os.path.join(args.output, 'centroids.npy')
        np.save(centroids_path, kmeans.centroids)
        print(f"\nCentroids saved to: {centroids_path}")
        
        # Save performance metrics
        metrics_path = os.path.join(args.output, 'performance_metrics.json')
        with open(metrics_path, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_summary = {
                k: (v.tolist() if isinstance(v, np.ndarray) else 
                    [float(x) for x in v] if isinstance(v, list) else 
                    float(v) if isinstance(v, (np.floating, np.integer)) else v)
                for k, v in perf_summary.items()
            }
            json.dump(json_summary, f, indent=2)
        print(f"Performance metrics saved to: {metrics_path}")
        
        # Save cluster assignments (sample for large datasets)
        assignments_path = os.path.join(args.output, 'cluster_assignments.txt')
        sample_size = min(10000, data_rdd.count())
        sample_assignments = labels_rdd.take(sample_size)
        with open(assignments_path, 'w') as f:
            for label in sample_assignments:
                f.write(f"{label}\n")
        print(f"Sample cluster assignments saved to: {assignments_path}")
        
        print(f"\n{'='*60}")
        print("Execution completed successfully!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        sc.stop()


if __name__ == "__main__":
    main()

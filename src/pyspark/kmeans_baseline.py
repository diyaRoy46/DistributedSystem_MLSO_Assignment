"""
Baseline single-node k-Means implementation for comparison.

This serves as the reference implementation to measure speedup
achieved by the distributed version.

Authors: Group 51
"""

import numpy as np
import time
import argparse
import json
import os
from sklearn.cluster import KMeans as SKLearnKMeans
import pandas as pd


class BaselineKMeans:
    """
    Single-node k-means implementation wrapping scikit-learn.
    
    This provides a fair comparison baseline with identical algorithm logic
    but without distributed execution.
    """
    
    def __init__(self, k: int, max_iterations: int = 20, 
                 tolerance: float = 1e-4, random_state: int = 42):
        """Initialize baseline k-means."""
        self.k = k
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.random_state = random_state
        
        self.model = SKLearnKMeans(
            n_clusters=k,
            max_iter=max_iterations,
            tol=tolerance,
            random_state=random_state,
            algorithm='lloyd',  # Use standard Lloyd's algorithm
            n_init=1  # Single initialization for fair comparison
        )
        
        self.training_time = None
        self.n_iterations = None
        
    def fit(self, data: np.ndarray, verbose: bool = True):
        """
        Train k-means model on single node.
        
        Args:
            data: Numpy array of shape (n_samples, n_features)
            verbose: Print progress
            
        Returns:
            self
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Baseline k-Means (Single-Node)")
            print(f"{'='*60}")
            print(f"Dataset size: {data.shape[0]:,} points")
            print(f"Dimensions: {data.shape[1]}")
            print(f"Number of clusters (k): {self.k}")
            print(f"Max iterations: {self.max_iterations}")
            print(f"{'='*60}\n")
        
        start_time = time.time()
        self.model.fit(data)
        self.training_time = time.time() - start_time
        self.n_iterations = self.model.n_iter_
        
        if verbose:
            print(f"Training completed in {self.training_time:.2f} seconds")
            print(f"Iterations: {self.n_iterations}")
            print(f"WCSS: {self.model.inertia_:,.2f}")
        
        return self
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        return self.model.predict(data)
    
    def get_centroids(self) -> np.ndarray:
        """Get cluster centroids."""
        return self.model.cluster_centers_
    
    def get_wcss(self) -> float:
        """Get Within-Cluster Sum of Squares."""
        return float(self.model.inertia_)
    
    def get_performance_summary(self) -> dict:
        """Get performance metrics."""
        return {
            'total_time': self.training_time,
            'n_iterations': int(self.n_iterations),
            'wcss': self.get_wcss(),
            'avg_iteration_time': self.training_time / self.n_iterations
        }


def load_data_from_csv(filepath: str) -> np.ndarray:
    """
    Load CSV data into numpy array.
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        Numpy array of shape (n_samples, n_features)
    """
    try:
        # Try loading with pandas first
        df = pd.read_csv(filepath, header=None)
        data = df.values
    except:
        # Fallback to numpy
        data = np.loadtxt(filepath, delimiter=',')
    
    return data


def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description='Baseline k-Means Clustering (Single-Node)'
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
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Baseline k-Means Clustering System (Single-Node)")
    print(f"{'='*60}")
    
    try:
        # Load data
        print(f"\nLoading data from: {args.input}")
        data = load_data_from_csv(args.input)
        print(f"Loaded {data.shape[0]:,} samples with {data.shape[1]} features")
        
        # Initialize and train model
        kmeans = BaselineKMeans(
            k=args.k,
            max_iterations=args.max_iterations,
            tolerance=args.tolerance
        )
        
        kmeans.fit(data, verbose=True)
        
        # Get predictions
        labels = kmeans.predict(data)
        
        # Get performance summary
        perf_summary = kmeans.get_performance_summary()
        
        # Save results
        os.makedirs(args.output, exist_ok=True)
        
        # Save centroids
        centroids_path = os.path.join(args.output, 'centroids.npy')
        np.save(centroids_path, kmeans.get_centroids())
        print(f"\nCentroids saved to: {centroids_path}")
        
        # Save performance metrics
        metrics_path = os.path.join(args.output, 'performance_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(perf_summary, f, indent=2)
        print(f"Performance metrics saved to: {metrics_path}")
        
        # Save cluster assignments
        assignments_path = os.path.join(args.output, 'cluster_assignments.txt')
        np.savetxt(assignments_path, labels, fmt='%d')
        print(f"Cluster assignments saved to: {assignments_path}")
        
        print(f"\n{'='*60}")
        print("Execution completed successfully!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    
if __name__ == "__main__":
    main()

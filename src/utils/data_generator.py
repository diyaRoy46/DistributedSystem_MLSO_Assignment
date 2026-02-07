"""
Synthetic customer segmentation data generator.

Generates realistic customer behavior data with known cluster structure
for testing the distributed k-means implementation.

Features represent typical e-commerce metrics:
- Total purchase amount
- Number of transactions
- Average session duration
- Days since last purchase
- Product category preferences

Authors: Group 51
"""

import numpy as np
import pandas as pd
import argparse
import os
from typing import Tuple


class CustomerDataGenerator:
    """
    Generate synthetic customer segmentation data with known clusters.
    
    This simulates realistic e-commerce customer behavior patterns:
    - High-value customers (frequent, high spend)
    - Regular customers (moderate activity)
    - Occasional shoppers (low frequency)
    - Dormant customers (inactive)
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize data generator."""
        self.random_state = random_state
        np.random.seed(random_state)
        
    def generate_cluster_data(self, n_samples: int, center: np.ndarray, 
                             std: float) -> np.ndarray:
        """
        Generate data points around a cluster center.
        
        Args:
            n_samples: Number of samples to generate
            center: Cluster center (mean vector)
            std: Standard deviation for Gaussian noise
            
        Returns:
            Array of generated points
        """
        n_features = len(center)
        data = np.random.randn(n_samples, n_features) * std + center
        
        # Ensure non-negative values for customer metrics
        data = np.abs(data)
        
        return data
    
    def generate_customer_segments(self, n_samples: int, 
                                   n_features: int = 10,
                                   n_clusters: int = 5,
                                   cluster_std: float = 1.0,
                                   balance: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate customer segmentation dataset with predefined clusters.
        
        Args:
            n_samples: Total number of customer records
            n_features: Number of features per customer
            n_clusters: Number of customer segments (clusters)
            cluster_std: Standard deviation of clusters
            balance: Whether to balance cluster sizes
            
        Returns:
            (data, true_labels) tuple
        """
        # Define cluster centers representing different customer segments
        np.random.seed(self.random_state)
        
        # Generate well-separated cluster centers
        cluster_centers = np.random.rand(n_clusters, n_features) * 10
        
        # Make clusters more distinct by scaling
        for i in range(n_clusters):
            cluster_centers[i] *= (i + 1) * 2
        
        # Determine samples per cluster
        if balance:
            samples_per_cluster = [n_samples // n_clusters] * n_clusters
            # Distribute remainder
            remainder = n_samples % n_clusters
            for i in range(remainder):
                samples_per_cluster[i] += 1
        else:
            # Imbalanced clusters (more realistic)
            weights = np.random.rand(n_clusters)
            weights /= weights.sum()
            samples_per_cluster = (weights * n_samples).astype(int)
            samples_per_cluster[-1] = n_samples - samples_per_cluster[:-1].sum()
        
        # Generate data for each cluster
        all_data = []
        all_labels = []
        
        for cluster_id in range(n_clusters):
            cluster_data = self.generate_cluster_data(
                samples_per_cluster[cluster_id],
                cluster_centers[cluster_id],
                cluster_std
            )
            all_data.append(cluster_data)
            all_labels.extend([cluster_id] * samples_per_cluster[cluster_id])
        
        # Combine all clusters
        data = np.vstack(all_data)
        labels = np.array(all_labels)
        
        # Shuffle data
        shuffle_idx = np.random.permutation(n_samples)
        data = data[shuffle_idx]
        labels = labels[shuffle_idx]
        
        return data, labels
    
    def add_noise_features(self, data: np.ndarray, 
                          n_noise_features: int = 0) -> np.ndarray:
        """
        Add random noise features to make clustering more challenging.
        
        Args:
            data: Original data
            n_noise_features: Number of noise features to add
            
        Returns:
            Data with noise features appended
        """
        if n_noise_features == 0:
            return data
        
        n_samples = data.shape[0]
        noise = np.random.randn(n_samples, n_noise_features)
        
        return np.hstack([data, noise])
    
    def generate_realistic_customer_data(self, n_samples: int) -> pd.DataFrame:
        """
        Generate realistic customer behavior data with meaningful features.
        
        Features:
        1. Total Purchase Amount ($)
        2. Number of Transactions
        3. Average Session Duration (minutes)
        4. Days Since Last Purchase
        5. Product Category 1 Preference (0-1)
        6. Product Category 2 Preference (0-1)
        7. Product Category 3 Preference (0-1)
        8. Click-Through Rate (0-1)
        9. Cart Abandonment Rate (0-1)
        10. Customer Lifetime (days)
        
        Returns:
            Pandas DataFrame with customer features
        """
        # Define customer segment prototypes
        segments = {
            'High-Value': {
                'total_purchase': (5000, 20000),
                'n_transactions': (20, 50),
                'avg_session_duration': (15, 45),
                'days_since_purchase': (1, 7),
                'category_pref_1': (0.6, 0.9),
                'category_pref_2': (0.4, 0.7),
                'category_pref_3': (0.3, 0.6),
                'click_through_rate': (0.3, 0.6),
                'cart_abandonment': (0.1, 0.3),
                'customer_lifetime': (365, 1095)
            },
            'Regular': {
                'total_purchase': (1000, 5000),
                'n_transactions': (10, 25),
                'avg_session_duration': (10, 30),
                'days_since_purchase': (7, 30),
                'category_pref_1': (0.4, 0.7),
                'category_pref_2': (0.3, 0.6),
                'category_pref_3': (0.2, 0.5),
                'click_through_rate': (0.2, 0.4),
                'cart_abandonment': (0.2, 0.4),
                'customer_lifetime': (180, 730)
            },
            'Occasional': {
                'total_purchase': (100, 1000),
                'n_transactions': (1, 10),
                'avg_session_duration': (5, 20),
                'days_since_purchase': (30, 90),
                'category_pref_1': (0.2, 0.5),
                'category_pref_2': (0.2, 0.5),
                'category_pref_3': (0.1, 0.4),
                'click_through_rate': (0.1, 0.3),
                'cart_abandonment': (0.3, 0.6),
                'customer_lifetime': (90, 365)
            },
            'Dormant': {
                'total_purchase': (50, 500),
                'n_transactions': (1, 5),
                'avg_session_duration': (2, 10),
                'days_since_purchase': (90, 365),
                'category_pref_1': (0.1, 0.3),
                'category_pref_2': (0.1, 0.3),
                'category_pref_3': (0.1, 0.3),
                'click_through_rate': (0.05, 0.15),
                'cart_abandonment': (0.5, 0.8),
                'customer_lifetime': (30, 180)
            },
            'New': {
                'total_purchase': (50, 500),
                'n_transactions': (1, 3),
                'avg_session_duration': (8, 25),
                'days_since_purchase': (1, 14),
                'category_pref_1': (0.3, 0.6),
                'category_pref_2': (0.2, 0.5),
                'category_pref_3': (0.1, 0.4),
                'click_through_rate': (0.2, 0.4),
                'cart_abandonment': (0.3, 0.5),
                'customer_lifetime': (7, 60)
            }
        }
        
        # Distribute samples across segments
        segment_names = list(segments.keys())
        n_segments = len(segment_names)
        samples_per_segment = n_samples // n_segments
        
        all_customers = []
        
        for segment_name in segment_names:
            segment_params = segments[segment_name]
            
            segment_data = {}
            for feature, (min_val, max_val) in segment_params.items():
                segment_data[feature] = np.random.uniform(
                    min_val, max_val, samples_per_segment
                )
            
            all_customers.append(pd.DataFrame(segment_data))
        
        # Handle remainder
        remainder = n_samples % n_segments
        if remainder > 0:
            extra_segment = segment_names[0]
            segment_params = segments[extra_segment]
            extra_data = {}
            for feature, (min_val, max_val) in segment_params.items():
                extra_data[feature] = np.random.uniform(min_val, max_val, remainder)
            all_customers.append(pd.DataFrame(extra_data))
        
        # Combine and shuffle
        df = pd.concat(all_customers, ignore_index=True)
        df = df.sample(frac=1, random_state=self.random_state).reset_index(drop=True)
        
        return df


def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description='Generate synthetic customer segmentation data'
    )
    parser.add_argument('--num-samples', type=int, default=100000,
                       help='Number of customer records (default: 100000)')
    parser.add_argument('--num-features', type=int, default=10,
                       help='Number of features (default: 10)')
    parser.add_argument('--num-clusters', type=int, default=5,
                       help='Number of true clusters (default: 5)')
    parser.add_argument('--cluster-std', type=float, default=1.0,
                       help='Cluster standard deviation (default: 1.0)')
    parser.add_argument('--output-dir', type=str, 
                       default='data/synthetic',
                       help='Output directory (default: data/synthetic)')
    parser.add_argument('--realistic', action='store_true',
                       help='Generate realistic customer features')
    parser.add_argument('--format', type=str, choices=['csv', 'numpy'], 
                       default='csv',
                       help='Output format (default: csv)')
    parser.add_argument('--random-state', type=int, default=42,
                       help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Customer Segmentation Data Generator")
    print(f"{'='*60}")
    print(f"Number of samples: {args.num_samples:,}")
    print(f"Number of features: {args.num_features}")
    print(f"Number of clusters: {args.num_clusters}")
    print(f"Cluster std dev: {args.cluster_std}")
    print(f"Output directory: {args.output_dir}")
    print(f"{'='*60}\n")
    
    # Initialize generator
    generator = CustomerDataGenerator(random_state=args.random_state)
    
    # Generate data
    print("Generating data...")
    
    if args.realistic:
        # Generate realistic customer data
        df = generator.generate_realistic_customer_data(args.num_samples)
        data = df.values
        true_labels = None  # Labels are implicit in segment structure
        
        print(f"Generated realistic customer data with {len(df.columns)} features:")
        print(f"  {', '.join(df.columns)}")
        
        # Save with feature names
        csv_path = os.path.join(args.output_dir, 'customer_data.csv')
        df.to_csv(csv_path, index=False)
        print(f"\nData saved to: {csv_path}")
        
        # Also save without header for easy loading
        csv_no_header = os.path.join(args.output_dir, 'data.csv')
        df.to_csv(csv_no_header, index=False, header=False)
        print(f"Data (no header) saved to: {csv_no_header}")
        
    else:
        # Generate synthetic clustered data
        data, true_labels = generator.generate_customer_segments(
            n_samples=args.num_samples,
            n_features=args.num_features,
            n_clusters=args.num_clusters,
            cluster_std=args.cluster_std,
            balance=True
        )
        
        print(f"Generated data shape: {data.shape}")
        print(f"Cluster distribution:")
        unique, counts = np.unique(true_labels, return_counts=True)
        for cluster_id, count in zip(unique, counts):
            print(f"  Cluster {cluster_id}: {count:,} samples ({count/len(true_labels)*100:.1f}%)")
        
        # Save data
        if args.format == 'csv':
            csv_path = os.path.join(args.output_dir, 'data.csv')
            np.savetxt(csv_path, data, delimiter=',', fmt='%.6f')
            print(f"\nData saved to: {csv_path}")
            
            # Save true labels
            labels_path = os.path.join(args.output_dir, 'true_labels.csv')
            np.savetxt(labels_path, true_labels, fmt='%d')
            print(f"True labels saved to: {labels_path}")
            
        else:  # numpy format
            npy_path = os.path.join(args.output_dir, 'data.npy')
            np.save(npy_path, data)
            print(f"\nData saved to: {npy_path}")
            
            labels_path = os.path.join(args.output_dir, 'true_labels.npy')
            np.save(labels_path, true_labels)
            print(f"True labels saved to: {labels_path}")
    
    # Save metadata
    metadata = {
        'n_samples': int(args.num_samples),
        'n_features': int(data.shape[1]),
        'n_clusters': int(args.num_clusters) if not args.realistic else 5,
        'cluster_std': float(args.cluster_std),
        'realistic': args.realistic,
        'random_state': args.random_state,
        'data_shape': list(data.shape)
    }
    
    import json
    metadata_path = os.path.join(args.output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")
    
    print(f"\n{'='*60}")
    print("Data generation completed successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

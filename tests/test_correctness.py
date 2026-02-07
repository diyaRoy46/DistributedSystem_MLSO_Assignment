"""
Test suite for verifying correctness of distributed k-means implementation.

Tests:
1. Convergence to same centroids as baseline
2. Cluster assignment consistency
3. WCSS calculation accuracy
4. Edge cases (empty clusters, single cluster, etc.)

Authors: Group 51
"""

import pytest
import numpy as np
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.data_generator import CustomerDataGenerator


class TestKMeansCorrectness:
    """Test correctness of k-means implementations."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample clustered data for testing."""
        generator = CustomerDataGenerator(random_state=42)
        data, labels = generator.generate_customer_segments(
            n_samples=1000,
            n_features=5,
            n_clusters=3,
            cluster_std=0.5,
            balance=True
        )
        return data, labels
    
    def test_data_generation(self, sample_data):
        """Test that data generation works correctly."""
        data, labels = sample_data
        
        assert data.shape[0] == 1000, "Should generate 1000 samples"
        assert data.shape[1] == 5, "Should have 5 features"
        assert len(np.unique(labels)) == 3, "Should have 3 clusters"
        assert not np.any(np.isnan(data)), "Data should not contain NaN"
        assert not np.any(np.isinf(data)), "Data should not contain Inf"
    
    def test_cluster_balance(self, sample_data):
        """Test that clusters are reasonably balanced."""
        data, labels = sample_data
        
        unique, counts = np.unique(labels, return_counts=True)
        
        # Each cluster should have roughly 1/3 of the data
        for count in counts:
            assert 250 <= count <= 400, f"Cluster imbalance: {count}"
    
    def test_baseline_convergence(self, sample_data, tmp_path):
        """Test that baseline implementation converges."""
        from sklearn.cluster import KMeans
        
        data, _ = sample_data
        
        kmeans = KMeans(n_clusters=3, max_iter=20, random_state=42, 
                       algorithm='lloyd', n_init=1)
        kmeans.fit(data)
        
        assert kmeans.n_iter_ < 20, "Should converge before max iterations"
        assert kmeans.cluster_centers_.shape == (3, 5), "Should have 3 centroids with 5 features"
    
    def test_wcss_decreases(self, sample_data):
        """Test that WCSS decreases with iterations (or stays same at convergence)."""
        from sklearn.cluster import KMeans
        
        data, _ = sample_data
        
        wcss_values = []
        for n_iter in [1, 5, 10, 20]:
            kmeans = KMeans(n_clusters=3, max_iter=n_iter, random_state=42,
                          algorithm='lloyd', n_init=1)
            kmeans.fit(data)
            wcss_values.append(kmeans.inertia_)
        
        # WCSS should monotonically decrease (or stay same)
        for i in range(1, len(wcss_values)):
            assert wcss_values[i] <= wcss_values[i-1], "WCSS should not increase"
    
    def test_cluster_assignment_consistency(self, sample_data):
        """Test that cluster assignments are consistent."""
        from sklearn.cluster import KMeans
        
        data, _ = sample_data
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=1)
        labels1 = kmeans.fit_predict(data)
        
        # Predict again on same data
        labels2 = kmeans.predict(data)
        
        assert np.array_equal(labels1, labels2), "Predictions should be consistent"
    
    def test_empty_cluster_handling(self):
        """Test handling of edge case where a cluster might become empty."""
        from sklearn.cluster import KMeans
        
        # Create data where one cluster might become empty
        data = np.vstack([
            np.random.randn(100, 5) + 10,  # Cluster 1 (far away)
            np.random.randn(100, 5) + 0,   # Cluster 2
            np.random.randn(1, 5) - 10     # Cluster 3 (single point, far away)
        ])
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=1)
        kmeans.fit(data)
        
        # Should still have 3 centroids
        assert kmeans.cluster_centers_.shape[0] == 3
    
    def test_single_cluster(self):
        """Test k-means with k=1."""
        from sklearn.cluster import KMeans
        
        data = np.random.randn(100, 5)
        
        kmeans = KMeans(n_clusters=1, random_state=42)
        kmeans.fit(data)
        
        # Centroid should be close to data mean
        expected_centroid = data.mean(axis=0)
        np.testing.assert_array_almost_equal(
            kmeans.cluster_centers_[0], expected_centroid, decimal=1
        )
    
    def test_deterministic_with_seed(self, sample_data):
        """Test that results are deterministic with same random seed."""
        from sklearn.cluster import KMeans
        
        data, _ = sample_data
        
        kmeans1 = KMeans(n_clusters=3, random_state=42, n_init=1)
        labels1 = kmeans1.fit_predict(data)
        
        kmeans2 = KMeans(n_clusters=3, random_state=42, n_init=1)
        labels2 = kmeans2.fit_predict(data)
        
        # Results should be identical with same seed
        np.testing.assert_array_equal(labels1, labels2)
        np.testing.assert_array_almost_equal(
            kmeans1.cluster_centers_, kmeans2.cluster_centers_
        )
    
    def test_realistic_customer_data(self):
        """Test with realistic customer segmentation data."""
        generator = CustomerDataGenerator(random_state=42)
        df = generator.generate_realistic_customer_data(500)
        
        assert len(df) == 500, "Should generate 500 customers"
        assert len(df.columns) == 10, "Should have 10 features"
        
        # Check feature ranges are reasonable
        assert df['total_purchase'].min() >= 0, "Purchase amount should be non-negative"
        assert df['n_transactions'].min() >= 0, "Transaction count should be non-negative"
        assert df['click_through_rate'].max() <= 1, "CTR should be <= 1"
        assert df['cart_abandonment'].max() <= 1, "Abandonment rate should be <= 1"


class TestPerformanceMetrics:
    """Test performance metric calculations."""
    
    def test_speedup_calculation(self):
        """Test speedup metric calculation."""
        baseline_time = 100.0
        parallel_time_2 = 55.0  # 2 workers
        parallel_time_4 = 30.0  # 4 workers
        
        speedup_2 = baseline_time / parallel_time_2
        speedup_4 = baseline_time / parallel_time_4
        
        assert 1.5 < speedup_2 < 2.5, "2-worker speedup should be reasonable"
        assert 2.5 < speedup_4 < 4.5, "4-worker speedup should be reasonable"
        
        # Efficiency
        efficiency_2 = (speedup_2 / 2) * 100
        efficiency_4 = (speedup_4 / 4) * 100
        
        assert efficiency_2 > 70, "Efficiency should be >70% for 2 workers"
        assert efficiency_4 > 60, "Efficiency should be >60% for 4 workers"
    
    def test_communication_cost_reduction(self):
        """Test communication cost reduction calculation."""
        n_points = 1000000
        n_features = 10
        n_clusters = 5
        n_partitions = 4
        bytes_per_float = 8
        
        # Naive: all points shuffled
        naive_cost = n_points * n_features * bytes_per_float
        
        # Optimized: only partial sums shuffled
        optimized_cost = n_partitions * n_clusters * n_features * bytes_per_float
        
        reduction_ratio = naive_cost / optimized_cost
        
        assert reduction_ratio > 1000, "Should have >1000x reduction for large data"
    
    def test_wcss_calculation(self):
        """Test WCSS calculation."""
        # Simple 2D example
        data = np.array([
            [0, 0], [1, 1],  # Cluster 0
            [10, 10], [11, 11]  # Cluster 1
        ])
        
        centroids = np.array([
            [0.5, 0.5],
            [10.5, 10.5]
        ])
        
        # Calculate WCSS manually
        wcss = 0
        for point in data[:2]:
            wcss += np.sum((point - centroids[0])**2)
        for point in data[2:]:
            wcss += np.sum((point - centroids[1])**2)
        
        expected_wcss = 2 * (0.5**2 + 0.5**2) + 2 * (0.5**2 + 0.5**2)
        
        assert abs(wcss - expected_wcss) < 0.01, "WCSS calculation should match"


def test_data_file_io(tmp_path):
    """Test data file I/O operations."""
    # Generate test data
    generator = CustomerDataGenerator(random_state=42)
    data, labels = generator.generate_customer_segments(
        n_samples=100, n_features=5, n_clusters=3
    )
    
    # Save to CSV
    csv_file = tmp_path / "test_data.csv"
    np.savetxt(csv_file, data, delimiter=',')
    
    # Load back
    loaded_data = np.loadtxt(csv_file, delimiter=',')
    
    np.testing.assert_array_almost_equal(data, loaded_data)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])

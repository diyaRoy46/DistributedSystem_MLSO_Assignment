"""
Visualization and analysis tools for experiment results.

Creates publication-quality plots for:
- Speedup analysis
- Scalability curves
- Convergence plots
- Communication cost comparison
- WCSS vs K (elbow method)

Authors: Group 51
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from typing import List, Dict
import glob


# Set style for publication-quality plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10


class ResultsVisualizer:
    """
    Visualization toolkit for distributed k-means experiment results.
    """
    
    def __init__(self, results_dir: str, output_dir: str = 'results/plots'):
        """
        Initialize visualizer.
        
        Args:
            results_dir: Directory containing experiment results
            output_dir: Directory to save plots
        """
        self.results_dir = results_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.results_data = self.load_all_results()
    
    def load_all_results(self) -> pd.DataFrame:
        """Load all experiment results into a DataFrame."""
        # Try to load summary CSV first
        summary_file = os.path.join(self.results_dir, 'summary.csv')
        if os.path.exists(summary_file):
            return pd.read_csv(summary_file)
        
        # Otherwise load from JSON
        json_file = os.path.join(self.results_dir, 'all_results.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                results = json.load(f)
            return pd.DataFrame(results)
        
        print("Warning: No results found")
        return pd.DataFrame()
    
    def plot_speedup_analysis(self, save: bool = True):
        """
        Create speedup plot showing parallel efficiency.
        
        Plots:
        - Actual speedup vs number of workers
        - Ideal linear speedup
        - Parallel efficiency percentage
        """
        # Filter speedup experiments
        speedup_data = self.results_data[
            self.results_data['name'].str.contains('Speedup', na=False)
        ].copy()
        
        if speedup_data.empty:
            print("No speedup data found")
            return
        
        # Sort by number of workers
        speedup_data = speedup_data.sort_values('num_workers')
        
        # Get baseline time (1 worker)
        baseline_time = speedup_data[speedup_data['num_workers'] == 1]['total_time'].values
        if len(baseline_time) == 0:
            print("Warning: No baseline (1 worker) found")
            baseline_time = speedup_data['total_time'].min()
        else:
            baseline_time = baseline_time[0]
        
        # Calculate speedup
        speedup_data['speedup'] = baseline_time / speedup_data['total_time']
        speedup_data['efficiency'] = (speedup_data['speedup'] / speedup_data['num_workers']) * 100
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Speedup
        workers = speedup_data['num_workers'].values
        actual_speedup = speedup_data['speedup'].values
        ideal_speedup = workers  # Linear speedup
        
        ax1.plot(workers, actual_speedup, 'o-', linewidth=2, markersize=8, 
                label='Actual Speedup', color='#2E86AB')
        ax1.plot(workers, ideal_speedup, '--', linewidth=2, 
                label='Ideal (Linear) Speedup', color='#A23B72')
        
        ax1.set_xlabel('Number of Workers')
        ax1.set_ylabel('Speedup')
        ax1.set_title('Speedup vs Number of Workers')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(workers)
        
        # Add speedup values as annotations
        for i, (w, s) in enumerate(zip(workers, actual_speedup)):
            ax1.annotate(f'{s:.2f}x', (w, s), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
        
        # Plot 2: Parallel Efficiency
        efficiency = speedup_data['efficiency'].values
        
        ax2.bar(workers, efficiency, color='#F18F01', alpha=0.7, edgecolor='black')
        ax2.axhline(y=100, color='#A23B72', linestyle='--', linewidth=2, 
                   label='100% Efficiency')
        ax2.axhline(y=80, color='green', linestyle=':', linewidth=1, 
                   label='80% Efficiency (Good)')
        
        ax2.set_xlabel('Number of Workers')
        ax2.set_ylabel('Parallel Efficiency (%)')
        ax2.set_title('Parallel Efficiency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(workers)
        ax2.set_ylim([0, 110])
        
        # Add efficiency values as annotations
        for i, (w, e) in enumerate(zip(workers, efficiency)):
            ax2.text(w, e + 2, f'{e:.1f}%', ha='center', fontsize=9)
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, 'speedup_analysis.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.show()
    
    def plot_scalability_analysis(self, save: bool = True):
        """
        Create scalability plot showing runtime vs dataset size.
        
        Compares distributed vs baseline implementations.
        """
        # Filter scalability experiments
        scalability_data = self.results_data[
            self.results_data['name'].str.contains('Scalability', na=False)
        ].copy()
        
        if scalability_data.empty:
            print("No scalability data found")
            return
        
        # Separate distributed and baseline
        distributed = scalability_data[
            scalability_data['implementation'] == 'distributed'
        ].sort_values('dataset_size')
        
        baseline = scalability_data[
            scalability_data['implementation'] == 'baseline'
        ].sort_values('dataset_size')
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if not distributed.empty:
            ax.plot(distributed['dataset_size'], distributed['total_time'], 
                   'o-', linewidth=2, markersize=8, label='Distributed (4 workers)',
                   color='#2E86AB')
        
        if not baseline.empty:
            ax.plot(baseline['dataset_size'], baseline['total_time'], 
                   's-', linewidth=2, markersize=8, label='Baseline (Single-node)',
                   color='#F18F01')
        
        ax.set_xlabel('Dataset Size (number of records)')
        ax.set_ylabel('Total Runtime (seconds)')
        ax.set_title('Scalability: Runtime vs Dataset Size')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Use log scale if data spans multiple orders of magnitude
        if distributed['dataset_size'].max() / distributed['dataset_size'].min() > 100:
            ax.set_xscale('log')
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, 'scalability_analysis.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.show()
    
    def plot_convergence(self, experiment_dir: str, save: bool = True):
        """
        Plot convergence history showing centroid shift over iterations.
        
        Args:
            experiment_dir: Directory of specific experiment with metrics
        """
        # Load metrics
        metrics_file = os.path.join(experiment_dir, 'performance_metrics.json')
        
        if not os.path.exists(metrics_file):
            print(f"Metrics file not found: {metrics_file}")
            return
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        if 'convergence_history' not in metrics:
            print("No convergence history found")
            return
        
        convergence = metrics['convergence_history']
        iterations = list(range(1, len(convergence) + 1))
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(iterations, convergence, 'o-', linewidth=2, markersize=6,
               color='#2E86AB')
        ax.axhline(y=metrics.get('tolerance', 1e-4), color='red', 
                  linestyle='--', label=f'Tolerance ({metrics.get("tolerance", 1e-4)})')
        
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Maximum Centroid Shift')
        ax.set_title('Convergence: Centroid Movement Over Iterations')
        ax.set_yscale('log')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, 'convergence_plot.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.show()
    
    def plot_communication_cost(self, save: bool = True):
        """
        Visualize communication cost reduction with combiners.
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Example calculation for demonstration
        # In practice, load this from actual metrics
        dataset_sizes = np.array([10000, 50000, 100000, 500000, 1000000])
        dimensions = 10
        k = 5
        num_partitions = 4
        
        # Without combiner: O(N*d)
        naive_cost = dataset_sizes * dimensions * 8 / (1024**2)  # MB
        
        # With combiner: O(M*K*d)
        optimized_cost = num_partitions * k * dimensions * 8 / (1024**2)  # MB
        optimized_cost = np.full_like(naive_cost, optimized_cost)
        
        ax.plot(dataset_sizes, naive_cost, 's-', linewidth=2, markersize=8,
               label='Without Combiner O(N·d)', color='#F18F01')
        ax.plot(dataset_sizes, optimized_cost, 'o-', linewidth=2, markersize=8,
               label='With Combiner O(M·K·d)', color='#2E86AB')
        
        ax.set_xlabel('Dataset Size (number of records)')
        ax.set_ylabel('Network Traffic per Iteration (MB)')
        ax.set_title('Communication Cost: Impact of Combiner Optimization')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        # Add reduction ratio annotation
        reduction = naive_cost[-1] / optimized_cost[-1]
        ax.text(dataset_sizes[-1], naive_cost[-1] * 0.7, 
               f'{reduction:.0f}x reduction', fontsize=12, color='green',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, 'communication_cost.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.show()
    
    def plot_cluster_quality(self, save: bool = True):
        """
        Plot WCSS vs number of clusters (elbow method).
        """
        # Filter cluster variation experiments
        cluster_data = self.results_data[
            self.results_data['name'].str.contains('Clusters_K', na=False)
        ].copy()
        
        if cluster_data.empty:
            print("No cluster variation data found")
            return
        
        cluster_data = cluster_data.sort_values('k')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(cluster_data['k'], cluster_data['wcss'], 'o-', 
               linewidth=2, markersize=10, color='#2E86AB')
        
        ax.set_xlabel('Number of Clusters (k)')
        ax.set_ylabel('Within-Cluster Sum of Squares (WCSS)')
        ax.set_title('Elbow Method: Optimal Number of Clusters')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(cluster_data['k'])
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, 'elbow_plot.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.show()
    
    def create_summary_table(self, save: bool = True):
        """
        Create a formatted summary table of all experiments.
        """
        if self.results_data.empty:
            print("No results to summarize")
            return
        
        # Select key columns
        summary_cols = ['name', 'implementation', 'dataset_size', 'k', 
                       'num_workers', 'total_time', 'iterations', 'wcss']
        
        available_cols = [col for col in summary_cols if col in self.results_data.columns]
        summary = self.results_data[available_cols].copy()
        
        # Format for display
        if 'total_time' in summary.columns:
            summary['total_time'] = summary['total_time'].apply(lambda x: f"{x:.2f}s" if pd.notna(x) else "N/A")
        if 'wcss' in summary.columns:
            summary['wcss'] = summary['wcss'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
        
        print("\n" + "="*80)
        print("EXPERIMENT SUMMARY")
        print("="*80)
        print(summary.to_string(index=False))
        print("="*80 + "\n")
        
        if save:
            filepath = os.path.join(self.output_dir, 'summary_table.txt')
            with open(filepath, 'w') as f:
                f.write(summary.to_string(index=False))
            print(f"Saved: {filepath}")
    
    def generate_all_plots(self):
        """Generate all visualization plots."""
        print("\nGenerating all visualizations...")
        print("="*60)
        
        try:
            print("\n1. Speedup Analysis...")
            self.plot_speedup_analysis()
        except Exception as e:
            print(f"   Error: {e}")
        
        try:
            print("\n2. Scalability Analysis...")
            self.plot_scalability_analysis()
        except Exception as e:
            print(f"   Error: {e}")
        
        try:
            print("\n3. Communication Cost...")
            self.plot_communication_cost()
        except Exception as e:
            print(f"   Error: {e}")
        
        try:
            print("\n4. Cluster Quality (Elbow)...")
            self.plot_cluster_quality()
        except Exception as e:
            print(f"   Error: {e}")
        
        try:
            print("\n5. Summary Table...")
            self.create_summary_table()
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n" + "="*60)
        print("All visualizations generated!")
        print(f"Saved to: {self.output_dir}")
        print("="*60 + "\n")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize distributed k-means experiment results'
    )
    parser.add_argument('--results-dir', type=str, 
                       default='results/experiments',
                       help='Directory containing experiment results')
    parser.add_argument('--output-dir', type=str, 
                       default='results/plots',
                       help='Directory to save plots')
    parser.add_argument('--plot-type', type=str, 
                       choices=['all', 'speedup', 'scalability', 'convergence', 
                               'communication', 'elbow'],
                       default='all',
                       help='Type of plot to generate')
    
    args = parser.parse_args()
    
    visualizer = ResultsVisualizer(args.results_dir, args.output_dir)
    
    if args.plot_type == 'all':
        visualizer.generate_all_plots()
    elif args.plot_type == 'speedup':
        visualizer.plot_speedup_analysis()
    elif args.plot_type == 'scalability':
        visualizer.plot_scalability_analysis()
    elif args.plot_type == 'communication':
        visualizer.plot_communication_cost()
    elif args.plot_type == 'elbow':
        visualizer.plot_cluster_quality()


if __name__ == "__main__":
    main()

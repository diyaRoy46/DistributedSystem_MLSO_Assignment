"""
Experiment runner for comprehensive performance evaluation.

Runs multiple experiments varying:
- Dataset sizes
- Number of workers
- Number of clusters
- Dimensionality

Authors: Group 51
"""

import os
import sys
import json
import time
import argparse
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime


class ExperimentRunner:
    """
    Automated experiment runner for distributed k-means evaluation.
    
    Systematically tests different configurations and collects metrics
    for speedup, communication cost, and scalability analysis.
    """
    
    def __init__(self, output_dir: str = 'results/experiments'):
        """Initialize experiment runner."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.results = []
        
    def run_single_experiment(self, config: dict) -> dict:
        """
        Run a single experiment configuration.
        
        Args:
            config: Experiment configuration dictionary
            
        Returns:
            Result metrics dictionary
        """
        print(f"\n{'='*60}")
        print(f"Running Experiment: {config['name']}")
        print(f"{'='*60}")
        print(f"Configuration:")
        for key, value in config.items():
            if key != 'name':
                print(f"  {key}: {value}")
        print(f"{'='*60}\n")
        
        # Create experiment output directory
        exp_name = config['name'].replace(' ', '_').lower()
        exp_dir = os.path.join(self.output_dir, exp_name)
        os.makedirs(exp_dir, exist_ok=True)
        
        # Determine which implementation to run
        implementation = config.get('implementation', 'distributed')
        
        if implementation == 'distributed':
            script_path = 'src/pyspark/kmeans_distributed.py'
            master = config.get('master', 'local[*]')
            
            # Build command
            cmd = [
                'spark-submit',
                '--master', master,
                script_path,
                '--input', config['input_data'],
                '--output', exp_dir,
                '--k', str(config['k']),
                '--max-iterations', str(config.get('max_iterations', 20)),
                '--tolerance', str(config.get('tolerance', 1e-4))
            ]
            
            if 'partitions' in config:
                cmd.extend(['--partitions', str(config['partitions'])])
                
        else:  # baseline
            script_path = 'src/pyspark/kmeans_baseline.py'
            
            cmd = [
                'python',
                script_path,
                '--input', config['input_data'],
                '--output', exp_dir,
                '--k', str(config['k']),
                '--max-iterations', str(config.get('max_iterations', 20)),
                '--tolerance', str(config.get('tolerance', 1e-4))
            ]
        
        # Run experiment
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0:
                success = True
                error_msg = None
                print(f"✓ Experiment completed successfully in {elapsed_time:.2f}s")
            else:
                success = False
                error_msg = result.stderr
                print(f"✗ Experiment failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            success = False
            error_msg = "Timeout"
            elapsed_time = 3600
            print(f"✗ Experiment timed out after 1 hour")
        except Exception as e:
            success = False
            error_msg = str(e)
            elapsed_time = time.time() - start_time
            print(f"✗ Experiment error: {error_msg}")
        
        # Load results if successful
        metrics = None
        if success:
            metrics_file = os.path.join(exp_dir, 'performance_metrics.json')
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
        
        # Compile result
        result_dict = {
            'name': config['name'],
            'implementation': implementation,
            'success': success,
            'elapsed_time': elapsed_time,
            'error': error_msg,
            **config,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result_dict)
        
        return result_dict
    
    def run_scalability_experiments(self, base_config: dict):
        """
        Run experiments to measure scalability with varying dataset sizes.
        
        Args:
            base_config: Base configuration to vary
        """
        print("\n" + "="*60)
        print("SCALABILITY EXPERIMENTS: Varying Dataset Size")
        print("="*60)
        
        sizes = [10000, 50000, 100000, 500000, 1000000]
        
        for size in sizes:
            # Generate data for this size
            data_dir = f'data/synthetic/size_{size}'
            os.makedirs(data_dir, exist_ok=True)
            
            data_file = os.path.join(data_dir, 'data.csv')
            
            if not os.path.exists(data_file):
                print(f"\nGenerating dataset with {size:,} samples...")
                gen_cmd = [
                    'python', 'src/utils/data_generator.py',
                    '--num-samples', str(size),
                    '--num-features', str(base_config.get('n_features', 10)),
                    '--num-clusters', str(base_config.get('k', 5)),
                    '--output-dir', data_dir
                ]
                subprocess.run(gen_cmd, check=True)
            
            # Run distributed version
            config_distributed = {
                'name': f'Scalability_Size_{size}_Distributed',
                'implementation': 'distributed',
                'input_data': data_file,
                'k': base_config.get('k', 5),
                'max_iterations': base_config.get('max_iterations', 20),
                'master': base_config.get('master', 'local[4]'),
                'partitions': base_config.get('partitions', 4),
                'dataset_size': size
            }
            
            self.run_single_experiment(config_distributed)
            
            # Run baseline for smaller datasets only (memory constraints)
            if size <= 100000:
                config_baseline = config_distributed.copy()
                config_baseline['name'] = f'Scalability_Size_{size}_Baseline'
                config_baseline['implementation'] = 'baseline'
                
                self.run_single_experiment(config_baseline)
    
    def run_speedup_experiments(self, base_config: dict):
        """
        Run experiments to measure speedup with varying worker counts.
        
        Args:
            base_config: Base configuration to vary
        """
        print("\n" + "="*60)
        print("SPEEDUP EXPERIMENTS: Varying Number of Workers")
        print("="*60)
        
        worker_configs = [
            {'workers': 1, 'master': 'local[1]'},
            {'workers': 2, 'master': 'local[2]'},
            {'workers': 4, 'master': 'local[4]'},
            {'workers': 8, 'master': 'local[8]'}
        ]
        
        # Use fixed dataset
        data_file = base_config['input_data']
        
        for worker_config in worker_configs:
            config = {
                'name': f'Speedup_{worker_config["workers"]}_Workers',
                'implementation': 'distributed',
                'input_data': data_file,
                'k': base_config.get('k', 5),
                'max_iterations': base_config.get('max_iterations', 20),
                'master': worker_config['master'],
                'partitions': worker_config['workers'],
                'num_workers': worker_config['workers']
            }
            
            self.run_single_experiment(config)
    
    def run_cluster_variation_experiments(self, base_config: dict):
        """
        Run experiments with varying numbers of clusters.
        
        Args:
            base_config: Base configuration to vary
        """
        print("\n" + "="*60)
        print("CLUSTER EXPERIMENTS: Varying Number of Clusters")
        print("="*60)
        
        k_values = [3, 5, 10, 20]
        
        data_file = base_config['input_data']
        
        for k in k_values:
            config = {
                'name': f'Clusters_K_{k}',
                'implementation': 'distributed',
                'input_data': data_file,
                'k': k,
                'max_iterations': base_config.get('max_iterations', 20),
                'master': base_config.get('master', 'local[4]'),
                'partitions': base_config.get('partitions', 4)
            }
            
            self.run_single_experiment(config)
    
    def save_results(self):
        """Save all experiment results to CSV and JSON."""
        # Save detailed JSON
        json_path = os.path.join(self.output_dir, 'all_results.json')
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {json_path}")
        
        # Create summary CSV
        summary_data = []
        for result in self.results:
            row = {
                'name': result['name'],
                'implementation': result['implementation'],
                'success': result['success'],
                'elapsed_time': result['elapsed_time'],
                'k': result.get('k'),
                'dataset_size': result.get('dataset_size', 'N/A'),
                'num_workers': result.get('num_workers', 'N/A')
            }
            
            if result['metrics']:
                row['total_time'] = result['metrics'].get('total_time', 'N/A')
                row['iterations'] = result['metrics'].get('total_iterations', 'N/A')
                row['wcss'] = result['metrics'].get('wcss', 'N/A')
                row['avg_iteration_time'] = result['metrics'].get('avg_iteration_time', 'N/A')
                
                if 'avg_network_reduction' in result['metrics']:
                    row['network_reduction'] = result['metrics']['avg_network_reduction']
            
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        csv_path = os.path.join(self.output_dir, 'summary.csv')
        df.to_csv(csv_path, index=False)
        print(f"Summary saved to: {csv_path}")
        
        # Print summary table
        print(f"\n{'='*60}")
        print("EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(df.to_string(index=False))
        print(f"{'='*60}\n")


def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description='Run comprehensive k-means experiments'
    )
    parser.add_argument('--experiment-type', type=str, 
                       choices=['all', 'scalability', 'speedup', 'clusters'],
                       default='all',
                       help='Type of experiments to run')
    parser.add_argument('--input-data', type=str, 
                       default='data/synthetic/data.csv',
                       help='Input data file for experiments')
    parser.add_argument('--output-dir', type=str, 
                       default='results/experiments',
                       help='Output directory for results')
    parser.add_argument('--k', type=int, default=5,
                       help='Number of clusters')
    parser.add_argument('--max-iterations', type=int, default=20,
                       help='Maximum iterations')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("DISTRIBUTED K-MEANS EXPERIMENT SUITE")
    print("="*60)
    print(f"Experiment type: {args.experiment_type}")
    print(f"Input data: {args.input_data}")
    print(f"Output directory: {args.output_dir}")
    print("="*60)
    
    # Initialize runner
    runner = ExperimentRunner(output_dir=args.output_dir)
    
    # Base configuration
    base_config = {
        'input_data': args.input_data,
        'k': args.k,
        'max_iterations': args.max_iterations,
        'master': 'local[4]',
        'partitions': 4
    }
    
    # Run experiments
    try:
        if args.experiment_type in ['all', 'scalability']:
            runner.run_scalability_experiments(base_config)
        
        if args.experiment_type in ['all', 'speedup']:
            runner.run_speedup_experiments(base_config)
        
        if args.experiment_type in ['all', 'clusters']:
            runner.run_cluster_variation_experiments(base_config)
        
        # Save all results
        runner.save_results()
        
        print("\n" + "="*60)
        print("ALL EXPERIMENTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running experiments: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hadoop Streaming Combiner for k-Means Clustering

COMBINER PHASE: Local aggregation to reduce network traffic.

This is the KEY OPTIMIZATION that reduces shuffle data from O(N*d) to O(M*K*d).

Input (stdin):  cluster_id<TAB>point_vector,count (sorted by key)
Output (stdout): cluster_id<TAB>sum_vector,total_count

The combiner aggregates all points assigned to the same cluster
within a single mapper partition, significantly reducing network traffic.

Authors: Group 51
"""

import sys
import numpy as np


def combiner():
    """
    Combiner function: Aggregate points locally before shuffle.
    
    Input: cluster_id<TAB>x1,x2,...,xn,count
    Output: cluster_id<TAB>sum1,sum2,...,sumn,total_count
    
    This local aggregation is the key optimization that makes
    distributed k-means bandwidth-efficient.
    """
    current_cluster = None
    current_sum = None
    current_count = 0
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            # Parse input: cluster_id<TAB>values
            cluster_id, values_str = line.split('\t', 1)
            cluster_id = int(cluster_id)
            
            # Parse values: last element is count, rest are point coordinates
            values = np.array([float(x) for x in values_str.split(',')])
            point_vector = values[:-1]
            count = int(values[-1])
            
            # If new cluster, emit previous aggregation
            if current_cluster is not None and cluster_id != current_cluster:
                # Emit aggregated result for previous cluster
                output_values = ','.join([str(x) for x in current_sum] + 
                                       [str(current_count)])
                print(f"{current_cluster}\t{output_values}")
                
                # Reset for new cluster
                current_sum = None
                current_count = 0
            
            # Update current cluster
            current_cluster = cluster_id
            
            # Aggregate (local sum and count)
            if current_sum is None:
                current_sum = point_vector.copy()
            else:
                current_sum += point_vector
            current_count += count
            
        except Exception as e:
            sys.stderr.write(f"Combiner error on line '{line}': {e}\n")
            continue
    
    # Emit final aggregation
    if current_cluster is not None:
        output_values = ','.join([str(x) for x in current_sum] + 
                               [str(current_count)])
        print(f"{current_cluster}\t{output_values}")


if __name__ == "__main__":
    combiner()

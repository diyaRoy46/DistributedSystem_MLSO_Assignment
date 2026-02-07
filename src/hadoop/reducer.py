#!/usr/bin/env python3
"""
Hadoop Streaming Reducer for k-Means Clustering

REDUCE PHASE: Global aggregation to compute new centroids.

Input (stdin):  cluster_id<TAB>sum_vector,count (sorted by key, from combiners)
Output (stdout): cluster_id<TAB>new_centroid

The reducer aggregates all partial sums from different mappers
to compute the final centroid position for each cluster.

Authors: Group 51
"""

import sys
import numpy as np


def reducer():
    """
    Reducer function: Compute new centroids from partial sums.
    
    Input: cluster_id<TAB>sum1,sum2,...,sumn,count
    Output: cluster_id<TAB>centroid1,centroid2,...,centroidn
    
    Aggregates all partial sums for each cluster and computes
    the mean to get the new centroid position.
    """
    current_cluster = None
    global_sum = None
    global_count = 0
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            # Parse input: cluster_id<TAB>values
            cluster_id, values_str = line.split('\t', 1)
            cluster_id = int(cluster_id)
            
            # Parse values: last element is count, rest are sum components
            values = np.array([float(x) for x in values_str.split(',')])
            partial_sum = values[:-1]
            count = int(values[-1])
            
            # If new cluster, emit centroid for previous cluster
            if current_cluster is not None and cluster_id != current_cluster:
                # Compute new centroid as mean
                if global_count > 0:
                    new_centroid = global_sum / global_count
                    output_values = ','.join([str(x) for x in new_centroid])
                    print(f"{current_cluster}\t{output_values}")
                else:
                    # Edge case: empty cluster (shouldn't happen normally)
                    sys.stderr.write(f"Warning: Cluster {current_cluster} is empty\n")
                
                # Reset for new cluster
                global_sum = None
                global_count = 0
            
            # Update current cluster
            current_cluster = cluster_id
            
            # Aggregate global sum and count
            if global_sum is None:
                global_sum = partial_sum.copy()
            else:
                global_sum += partial_sum
            global_count += count
            
        except Exception as e:
            sys.stderr.write(f"Reducer error on line '{line}': {e}\n")
            continue
    
    # Emit final centroid
    if current_cluster is not None and global_count > 0:
        new_centroid = global_sum / global_count
        output_values = ','.join([str(x) for x in new_centroid])
        print(f"{current_cluster}\t{output_values}")


if __name__ == "__main__":
    reducer()

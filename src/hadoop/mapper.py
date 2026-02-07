#!/usr/bin/env python3
"""
Hadoop Streaming Mapper for k-Means Clustering

MAP PHASE: Assigns each data point to its nearest centroid.

Input (stdin):  CSV line representing a data point
Output (stdout): cluster_id<TAB>point_vector,1

The mapper reads the current centroids from a broadcast file
and emits (cluster_id, (point, count=1)) for each input point.

Authors: Group 51
"""

import sys
import numpy as np
import os


def load_centroids(centroids_file='centroids.txt'):
    """
    Load current centroids from distributed cache file.
    
    In Hadoop streaming, centroids are distributed via -cacheFile option.
    
    Returns:
        numpy array of centroids (k x d)
    """
    centroids = []
    with open(centroids_file, 'r') as f:
        for line in f:
            centroid = np.array([float(x) for x in line.strip().split(',')])
            centroids.append(centroid)
    return np.array(centroids)


def find_nearest_centroid(point, centroids):
    """
    Find index of nearest centroid to given point.
    
    Args:
        point: Data point (numpy array)
        centroids: Array of centroids
        
    Returns:
        Index of nearest centroid
    """
    distances = np.linalg.norm(centroids - point, axis=1)
    return int(np.argmin(distances))


def mapper():
    """
    Map function: Read points from stdin, emit (cluster_id, point_data).
    
    Output format: cluster_id<TAB>x1,x2,...,xn,1
    The final 1 represents the count for this point.
    """
    # Load centroids from distributed cache
    centroids = load_centroids()
    
    # Read input from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            # Parse data point
            point = np.array([float(x) for x in line.split(',')])
            
            # Find nearest centroid
            cluster_id = find_nearest_centroid(point, centroids)
            
            # Emit: cluster_id<TAB>point_vector,count
            # We append count=1 to the point vector
            output_values = ','.join([str(x) for x in point] + ['1'])
            print(f"{cluster_id}\t{output_values}")
            
        except Exception as e:
            # Log errors to stderr (won't affect output)
            sys.stderr.write(f"Mapper error on line '{line}': {e}\n")
            continue


if __name__ == "__main__":
    mapper()

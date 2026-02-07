#!/bin/bash
#
# Hadoop Streaming k-Means Driver Script
#
# This script orchestrates the iterative k-means algorithm using Hadoop streaming.
# It runs multiple MapReduce jobs until convergence.
#
# Usage: ./run_hadoop_kmeans.sh <input_data> <output_dir> <k> <max_iterations>
#
# Authors: Group 51

set -e  # Exit on error

# Parse arguments
INPUT_DATA=$1
OUTPUT_DIR=$2
K=${3:-5}
MAX_ITERATIONS=${4:-20}
TOLERANCE=${5:-0.0001}

echo "================================"
echo "Hadoop Streaming k-Means"
echo "================================"
echo "Input: $INPUT_DATA"
echo "Output: $OUTPUT_DIR"
echo "Clusters (k): $K"
echo "Max iterations: $MAX_ITERATIONS"
echo "Tolerance: $TOLERANCE"
echo "================================"

# Create output directory
mkdir -p $OUTPUT_DIR

# Initialize centroids (random selection from data)
echo "Initializing centroids..."
CENTROIDS_FILE="$OUTPUT_DIR/centroids_0.txt"
head -n $K $INPUT_DATA > $CENTROIDS_FILE

# Iterative refinement
ITERATION=0
CONVERGED=0

while [ $ITERATION -lt $MAX_ITERATIONS ] && [ $CONVERGED -eq 0 ]; do
    echo ""
    echo "Iteration $((ITERATION + 1))/$MAX_ITERATIONS"
    echo "----------------------------"
    
    # Prepare paths
    CURRENT_CENTROIDS="$OUTPUT_DIR/centroids_$ITERATION.txt"
    ITER_OUTPUT="$OUTPUT_DIR/iteration_$ITERATION"
    NEW_CENTROIDS="$OUTPUT_DIR/centroids_$((ITERATION + 1)).txt"
    
    # Run MapReduce job
    echo "Running MapReduce job..."
    
    hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
        -input $INPUT_DATA \
        -output $ITER_OUTPUT \
        -mapper "python3 src/hadoop/mapper.py" \
        -combiner "python3 src/hadoop/combiner.py" \
        -reducer "python3 src/hadoop/reducer.py" \
        -file src/hadoop/mapper.py \
        -file src/hadoop/combiner.py \
        -file src/hadoop/reducer.py \
        -file $CURRENT_CENTROIDS \
        -cmdenv CENTROIDS_FILE=centroids_$ITERATION.txt
    
    # Extract new centroids from output
    echo "Extracting new centroids..."
    hdfs dfs -cat $ITER_OUTPUT/part-* | \
        sort -n -k1 | \
        cut -f2 > $NEW_CENTROIDS
    
    # Check convergence (compute centroid shift)
    echo "Checking convergence..."
    SHIFT=$(python3 -c "
import numpy as np
old = np.loadtxt('$CURRENT_CENTROIDS', delimiter=',')
new = np.loadtxt('$NEW_CENTROIDS', delimiter=',')
shift = np.max(np.linalg.norm(old - new, axis=1))
print(shift)
")
    
    echo "Centroid shift: $SHIFT"
    
    # Check if converged
    if (( $(echo "$SHIFT < $TOLERANCE" | bc -l) )); then
        echo "Converged!"
        CONVERGED=1
    fi
    
    ITERATION=$((ITERATION + 1))
done

# Save final centroids
cp $OUTPUT_DIR/centroids_$ITERATION.txt $OUTPUT_DIR/final_centroids.txt

echo ""
echo "================================"
echo "k-Means completed"
echo "Iterations: $ITERATION"
echo "Final centroids: $OUTPUT_DIR/final_centroids.txt"
echo "================================"

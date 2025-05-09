#!/bin/bash

# Mary Bird Perkins QR Code Generator - Batch Mode
# This script runs the batch QR code generator for multiple URLs

# Try to use conda environment if available
if command -v conda &> /dev/null && conda info --envs | grep -q "QRC"; then
    # Use conda environment
    conda run -n QRC python batch_generate.py "$@"
elif [ -d "$(conda info --base)/envs/QRC" ]; then
    # Use full path to conda environment
    "$(conda info --base)/envs/QRC/bin/python" batch_generate.py "$@"
else
    # Fall back to system Python
    python batch_generate.py "$@"
fi

echo "QR codes have been generated in the Generated_QR directory."
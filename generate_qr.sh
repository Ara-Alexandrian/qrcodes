#!/bin/bash

# Mary Bird Perkins QR Code Generator - Single Mode
# This script runs the QR code generator for a single URL

# Try to use conda environment if available
if command -v conda &> /dev/null && conda info --envs | grep -q "QRC"; then
    # Use conda environment
    conda run -n QRC python qr_generator.py
elif [ -d "$(conda info --base)/envs/QRC" ]; then
    # Use full path to conda environment
    "$(conda info --base)/envs/QRC/bin/python" qr_generator.py
else
    # Fall back to system Python
    python qr_generator.py
fi

echo "QR code has been generated in the Generated_QR directory."
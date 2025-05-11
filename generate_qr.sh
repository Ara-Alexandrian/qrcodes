#!/bin/bash

# Mary Bird Perkins QR Code Generator - Single Mode
# This script runs the QR code generator for a single URL

# Parameters
URL="${1:-}"
MFR="${2:-}"
MODEL="${3:-}"
SERIAL="${4:-}"
OUTPUT_DIR="Generated_QR"

# Check if URL parameter is provided
if [ -z "$URL" ]; then
    echo "Error: URL parameter is required."
    echo "Usage: $0 <url> [manufacturer] [model] [serial]"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate a unique output path
OUTPUT_PATH="$OUTPUT_DIR/qr_$(echo -n "$URL" | md5sum | cut -c1-8).png"

echo "Generating QR code for URL: $URL"
echo "Manufacturer: $MFR"
echo "Model: $MODEL"
echo "Serial: $SERIAL"
echo "Output Path: $OUTPUT_PATH"

# Try to use conda environment if available
if command -v conda &> /dev/null && conda info --envs | grep -q "QRC"; then
    # Use conda environment
    conda run -n QRC python -c "from qr_generator import create_qr_in_flame; import os; logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources', 'Mary Bird Perkins Cancer Center.png'); create_qr_in_flame(logo_path, '$URL', '$OUTPUT_PATH', '$MFR', '$MODEL', '$SERIAL')"
elif [ -d "$(conda info --base)/envs/QRC" ]; then
    # Use full path to conda environment
    "$(conda info --base)/envs/QRC/bin/python" -c "from qr_generator import create_qr_in_flame; import os; logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources', 'Mary Bird Perkins Cancer Center.png'); create_qr_in_flame(logo_path, '$URL', '$OUTPUT_PATH', '$MFR', '$MODEL', '$SERIAL')"
else
    # Fall back to system Python
    python -c "from qr_generator import create_qr_in_flame; import os; logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources', 'Mary Bird Perkins Cancer Center.png'); create_qr_in_flame(logo_path, '$URL', '$OUTPUT_PATH', '$MFR', '$MODEL', '$SERIAL')"
fi

# Check if generation was successful
if [ -f "$OUTPUT_PATH" ]; then
    echo "QR code has been generated successfully: $OUTPUT_PATH"
else
    echo "Error: Failed to generate QR code."
    exit 1
fi
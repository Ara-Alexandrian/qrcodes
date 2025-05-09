#!/usr/bin/env python
"""
Batch QR code generator for Mary Bird Perkins Cancer Center logo
This script generates multiple QR codes for a list of URLs
"""
import os
import sys
import argparse
from qr_generator import create_qr_in_flame

def main():
    parser = argparse.ArgumentParser(description='Generate QR codes within the Mary Bird Perkins logo flame')
    parser.add_argument('-f', '--file', help='File containing URLs (one per line)')
    parser.add_argument('-u', '--urls', nargs='+', help='List of URLs to encode')
    parser.add_argument('-o', '--output', default='Generated_QR', help='Output directory')
    parser.add_argument('-m', '--manufacturer', default="", help='Equipment manufacturer name')
    parser.add_argument('-d', '--model', default="", help='Equipment model number')
    parser.add_argument('-s', '--serial', default="", help='Equipment serial number')
    
    args = parser.parse_args()
    
    if not args.file and not args.urls:
        parser.print_help()
        print("\nError: You must provide either a file with URLs or a list of URLs")
        sys.exit(1)
        
    urls = []
    
    # Get URLs from file if provided
    if args.file:
        try:
            with open(args.file, 'r') as f:
                urls.extend([line.strip() for line in f if line.strip()])
        except FileNotFoundError:
            print(f"Error: File {args.file} not found")
            sys.exit(1)
    
    # Add URLs from command line
    if args.urls:
        urls.extend(args.urls)
    
    # Remove duplicates while preserving order
    urls = list(dict.fromkeys(urls))
    
    if not urls:
        print("No valid URLs found. Exiting.")
        sys.exit(1)
    
    # Create output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, 'Resources', 'Mary Bird Perkins Cancer Center.png')
    output_dir = os.path.join(script_dir, args.output)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate QR codes for each URL
    for url in urls:
        print(f"Generating QR code for: {url}")
        output_path = os.path.join(output_dir, f'qr_in_flame_{hash(url) % 10000}.png')
        created_file = create_qr_in_flame(logo_path, url, output_path, 
                                         args.manufacturer, args.model, args.serial)
        print(f"  → Created: {created_file}")
    
    print(f"\nGenerated {len(urls)} QR codes in {output_dir}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Analyze GTA IV DLC and Update ZIP contents for hash implementation"""

import zipfile
import os
import hashlib
import sys

DLC_PATH = '/Users/Ozordi/Downloads/LibertyRecomp/gta_iv/dlcs'
UPDATE_PATH = '/Users/Ozordi/Downloads/LibertyRecomp/gta_iv/updates'

def analyze_zip(zip_path):
    """Analyze contents of a ZIP file"""
    print(f"\n{'='*60}")
    print(f"File: {os.path.basename(zip_path)}")
    print(f"Size: {os.path.getsize(zip_path):,} bytes")
    print(f"{'='*60}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            files = []
            for name in z.namelist():
                info = z.getinfo(name)
                if not name.endswith('/'):  # Skip directories
                    files.append({
                        'name': name,
                        'size': info.file_size,
                        'compressed': info.compress_size
                    })
            
            print(f"Total files: {len(files)}")
            print(f"\nFiles (first 30):")
            for f in files[:30]:
                print(f"  {f['name']}")
                print(f"    Size: {f['size']:,} bytes, Compressed: {f['compressed']:,}")
            
            if len(files) > 30:
                print(f"  ... and {len(files) - 30} more files")
                
            return files
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("=== GTA IV DLC Analysis ===")
    
    if os.path.exists(DLC_PATH):
        for f in sorted(os.listdir(DLC_PATH)):
            if f.endswith('.zip'):
                analyze_zip(os.path.join(DLC_PATH, f))
    
    print("\n\n=== GTA IV Update Analysis ===")
    
    if os.path.exists(UPDATE_PATH):
        for f in sorted(os.listdir(UPDATE_PATH)):
            if f.endswith('.zip'):
                analyze_zip(os.path.join(UPDATE_PATH, f))

if __name__ == '__main__':
    main()

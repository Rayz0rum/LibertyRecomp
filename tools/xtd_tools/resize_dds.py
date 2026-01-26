#!/usr/bin/env python3
"""
Resize oversized DDS files to 64x64 before XTD conversion.
Detects actual size from data length, not header (some FusionFix files have wrong headers).
"""

import os
import struct
from pathlib import Path

SOURCE_DIR = Path("/Users/Ozordi/Downloads/LibertyRecomp/tools/GTAIV.EFLC.FusionFix-master/textures/pc/textures/buttons_360.wtd")
PROCESSED_DIR = Path("/Users/Ozordi/Downloads/LibertyRecomp/tools/xtd_tools/processed_dds")

def create_64x64_dds_header():
    """Create a DXT5 DDS header for 64x64 texture"""
    header = bytearray(128)
    header[0:4] = b'DDS '
    struct.pack_into('<I', header, 4, 124)  # Size
    struct.pack_into('<I', header, 8, 0x1007)  # Flags
    struct.pack_into('<I', header, 12, 64)  # Height
    struct.pack_into('<I', header, 16, 64)  # Width
    struct.pack_into('<I', header, 20, 4096)  # Linear size (64x64 DXT5)
    struct.pack_into('<I', header, 76, 32)  # Pixel format size
    struct.pack_into('<I', header, 80, 0x4)  # DDPF_FOURCC
    header[84:88] = b'DXT5'
    struct.pack_into('<I', header, 108, 0x1000)  # Caps
    return bytes(header)

def resize_128_to_64(data_128x128):
    """
    Resize 128x128 DXT5 to 64x64 by taking every other block.
    """
    block_size = 16
    src_blocks_per_row = 32  # 128/4
    dst_blocks_per_row = 16  # 64/4
    
    output = bytearray(dst_blocks_per_row * dst_blocks_per_row * block_size)
    
    for dst_y in range(dst_blocks_per_row):
        for dst_x in range(dst_blocks_per_row):
            src_x = dst_x * 2
            src_y = dst_y * 2
            src_offset = (src_x + src_y * src_blocks_per_row) * block_size
            dst_offset = (dst_x + dst_y * dst_blocks_per_row) * block_size
            output[dst_offset:dst_offset+block_size] = data_128x128[src_offset:src_offset+block_size]
    
    return bytes(output)

def process_file(src_path, dst_path):
    """Process a single DDS file"""
    with open(src_path, 'rb') as f:
        data = f.read()
    
    if data[:4] != b'DDS ':
        print(f"  SKIP {src_path.name}: Invalid DDS")
        return False
    
    pixel_data = data[128:]
    data_size = len(pixel_data)
    
    # Detect actual size by data length:
    # 64x64 DXT5 = 16x16 blocks * 16 bytes = 4096 bytes
    # 128x128 DXT5 = 32x32 blocks * 16 bytes = 16384 bytes
    
    if data_size == 4096:
        # Correct 64x64, just copy
        with open(dst_path, 'wb') as f:
            f.write(data)
        return True
    
    if data_size == 16384:
        # Actually 128x128 data, resize it
        resized = resize_128_to_64(pixel_data)
        new_header = create_64x64_dds_header()
        with open(dst_path, 'wb') as f:
            f.write(new_header)
            f.write(resized)
        print(f"  RESIZED {src_path.name}: 128x128 data -> 64x64")
        return True
    
    if data_size > 4096:
        # Has mipmaps or other size, take first 4096 bytes only
        new_header = create_64x64_dds_header()
        with open(dst_path, 'wb') as f:
            f.write(new_header)
            f.write(pixel_data[:4096])
        print(f"  TRUNCATED {src_path.name}: {data_size} bytes -> 4096")
        return True
    
    print(f"  SKIP {src_path.name}: Unexpected data size {data_size}")
    return False

def main():
    import shutil
    
    # Clean and recreate output directory
    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)
    PROCESSED_DIR.mkdir(exist_ok=True)
    
    print("Processing DDS files for XTD conversion...")
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {PROCESSED_DIR}")
    
    resized_count = 0
    copied_count = 0
    
    for dds_file in sorted(SOURCE_DIR.glob("*.dds")):
        # Skip large/irrelevant files
        if "controller" in dds_file.name.lower():
            continue
        if "key_" in dds_file.name.lower():
            continue
        
        dst_path = PROCESSED_DIR / dds_file.name
        with open(dds_file, 'rb') as f:
            size = len(f.read())
        
        if size > 4224:
            if process_file(dds_file, dst_path):
                resized_count += 1
        else:
            # Just copy small files
            shutil.copy(dds_file, dst_path)
            copied_count += 1
    
    print(f"\nResized: {resized_count}")
    print(f"Copied: {copied_count}")
    print(f"Total: {len(list(PROCESSED_DIR.glob('*.dds')))}")

if __name__ == "__main__":
    main()

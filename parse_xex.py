import struct
import sys

def parse_xex(file_path):
    with open(file_path, "rb") as f:
        # MAGIC
        magic = f.read(4)
        if magic not in (b"XEX2", b"XEX1"):
            print(f"Invalid magic: {magic}")
            return
        
        f.seek(0x10)
        security_info_offset, = struct.unpack(">I", f.read(4))
        
        f.seek(security_info_offset)
        sec_size, = struct.unpack(">I", f.read(4))
        image_size, = struct.unpack(">I", f.read(4))
        print(f"Image Size from Security Info: {hex(image_size)}")
        
        f.seek(security_info_offset + 0x10)
        page_descriptor_count, = struct.unpack(">I", f.read(4))
        
        total_size = 0
        for i in range(page_descriptor_count):
            desc, = struct.unpack(">I", f.read(4))
            desc_info = desc >> 28
            page_count = desc & 0x0FFFFFFF
            total_size += page_count * 4096
            
        print(f"Total Size from Page Descriptors: {hex(total_size)}")

parse_xex("glue/rexglue-sdk-main/gta4-recomp/assets/default_v8.xex")

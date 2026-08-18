#!/usr/bin/env python3
"""
Meli v1.0.0 Windows Self-Contained Release Packager
Collects the compiled release executable, WebView2 loader, and LLVM-MinGW runtime DLLs
into a standalone, redistributable directory.
"""

import os
import sys
import shutil
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TARGET_RELEASE = Path("C:/Users/Public/meli_target/release")
TOOLCHAIN_BIN = Path(r"C:\Users\Swastik Pandey\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260616-ucrt-x86_64\bin")
OUTPUT_DIR = WORKSPACE_ROOT / "release" / "meli-v1.0.0-windows-x64"

def get_imported_dlls(pe_path: Path):
    with open(pe_path, 'rb') as f:
        data = f.read()
    if data[:2] != b'MZ':
        return []
    e_lfanew = struct.unpack('<I', data[0x3C:0x40])[0]
    if data[e_lfanew:e_lfanew+4] != b'PE\x00\x00':
        return []
    num_sections = struct.unpack('<H', data[e_lfanew+6:e_lfanew+8])[0]
    opt_header_size = struct.unpack('<H', data[e_lfanew+20:e_lfanew+22])[0]
    opt_header_offset = e_lfanew + 24
    magic = struct.unpack('<H', data[opt_header_offset:opt_header_offset+2])[0]
    is_64 = (magic == 0x20B)
    import_dir_rva = struct.unpack('<I', data[opt_header_offset+(120 if is_64 else 104):opt_header_offset+(124 if is_64 else 108)])[0]
    if import_dir_rva == 0:
        return []
    section_headers_offset = opt_header_offset + opt_header_size
    sections = []
    for i in range(num_sections):
        s_offset = section_headers_offset + i * 40
        s_vsize, s_vaddr, s_rawsize, s_rawoffset = struct.unpack('<IIII', data[s_offset+8:s_offset+24])
        sections.append((s_vaddr, s_vsize, s_rawoffset, s_rawsize))
    def rva_to_offset(rva):
        for vaddr, vsize, rawoffset, rawsize in sections:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                return rawoffset + (rva - vaddr)
        return None
    import_offset = rva_to_offset(import_dir_rva)
    if not import_offset:
        return []
    dlls = []
    curr = import_offset
    while True:
        desc = data[curr:curr+20]
        if desc == b'\x00'*20:
            break
        ilt_rva, time_date, forwarder, name_rva, iat_rva = struct.unpack('<IIIII', desc)
        name_offset = rva_to_offset(name_rva)
        if name_offset:
            end = data.find(b'\x00', name_offset)
            dll_name = data[name_offset:end].decode('ascii', errors='ignore')
            dlls.append(dll_name)
        curr += 20
    return dlls

def package_release():
    print(f"=== Meli v1.0.0 Standalone Windows Packager ===")
    
    exe_src = TARGET_RELEASE / "meli-app.exe"
    if not exe_src.exists():
        print(f"ERROR: Release binary not found at {exe_src}. Please run cargo build --release first.")
        sys.exit(1)
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy meli-app.exe
    exe_dst = OUTPUT_DIR / "meli-app.exe"
    shutil.copy2(exe_src, exe_dst)
    print(f"[OK] Copied executable: {exe_dst} ({exe_dst.stat().st_size / (1024*1024):.2f} MB)")
    
    # 2. Inspect dependencies
    imports = get_imported_dlls(exe_dst)
    print(f"[OK] Detected PE imports ({len(imports)} DLLs):")
    for imp in imports:
        print(f"   - {imp}")
        
    # 3. Copy required runtime DLLs
    runtime_dlls = ["libunwind.dll", "libc++.dll", "WebView2Loader.dll"]
    for dll in runtime_dlls:
        src = None
        if (TOOLCHAIN_BIN / dll).exists():
            src = TOOLCHAIN_BIN / dll
        elif (TARGET_RELEASE / dll).exists():
            src = TARGET_RELEASE / dll
            
        if src and src.exists():
            dst = OUTPUT_DIR / dll
            shutil.copy2(src, dst)
            # Also keep target directory synchronized if src came from toolchain
            target_dst = TARGET_RELEASE / dll
            if src.resolve() != target_dst.resolve():
                shutil.copy2(src, target_dst)
            sha = hashlib.sha256(open(dst, 'rb').read()).hexdigest()[:12]
            print(f"[OK] Copied runtime DLL: {dll} (SHA: {sha})")
        else:
            print(f"[WARN] Could not locate runtime DLL: {dll}")
            
    # 4. Copy docs and licenses
    for doc in ["README.md", "LICENSE"]:
        src = WORKSPACE_ROOT / doc
        if src.exists():
            shutil.copy2(src, OUTPUT_DIR / doc)
            print(f"[OK] Bundled doc: {doc}")
            
    # 5. Create redistributable ZIP archive
    zip_dst = WORKSPACE_ROOT / "release" / "Meli-v1.0.0-windows-x64.zip"
    import zipfile
    with zipfile.ZipFile(zip_dst, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for f in sorted(files):
                full_path = Path(root) / f
                rel_path = full_path.relative_to(OUTPUT_DIR.parent)
                zf.write(full_path, arcname=str(rel_path))
    print(f"[OK] Created distributable archive: {zip_dst} ({zip_dst.stat().st_size / (1024*1024):.2f} MB)")
            
    print(f"\n[SUCCESS] Standalone release package ready at:\n   {OUTPUT_DIR.resolve()}\n")
    print(f"Package contents:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        print(f" - {f.name:20s} ({f.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    package_release()

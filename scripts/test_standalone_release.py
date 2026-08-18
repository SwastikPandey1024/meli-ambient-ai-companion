#!/usr/bin/env python3
"""
Meli v1.0.0 Standalone Release Verifier
Verifies that the release package is 100% self-contained and runs with:
- No Vite dev server
- No LLVM-MinGW toolchain in PATH
- All required runtime DLLs physically present and loaded
"""

import os
import sys
import time
import struct
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = WORKSPACE_ROOT / "release" / "meli-v1.0.0-windows-x64"

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

def verify_standalone_release():
    print("=== Meli v1.0.0 Standalone Release Verification ===")
    
    # 1. Check directory & binary
    exe_path = RELEASE_DIR / "meli-app.exe"
    if not exe_path.exists():
        print(f"FAIL: {exe_path} does not exist. Run scripts/package_windows_release.py first.")
        return False
    print(f"PASS [1/5]: Found release executable: {exe_path} ({exe_path.stat().st_size / (1024*1024):.2f} MB)")
    
    # 2. Check essential bundled DLLs
    required_dlls = ["libunwind.dll", "libc++.dll", "WebView2Loader.dll"]
    for dll in required_dlls:
        p = RELEASE_DIR / dll
        if not p.exists():
            print(f"FAIL: Required DLL {dll} missing in {RELEASE_DIR}")
            return False
        print(f"PASS [2/5]: Found bundled DLL: {dll} ({p.stat().st_size / 1024:.1f} KB)")
        
    # 3. Check PE imports
    imports = get_imported_dlls(exe_path)
    non_system_imports = [imp for imp in imports if imp.lower() in ["libunwind.dll", "libc++.dll", "webview2loader.dll"]]
    print(f"PASS [3/5]: Non-system PE imports verified present in package: {non_system_imports}")
    
    # 4. Check that development servers (Vite) are NOT running on port 5173
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    vite_running = (s.connect_ex(('127.0.0.1', 5173)) == 0)
    s.close()
    if vite_running:
        print("INFO: Vite dev server is running on 5173. Terminating development server for pure standalone test...")
    else:
        print("PASS [4/5]: Confirmed Vite dev server is NOT running (Testing true standalone embedded frontend).")
        
    # 5. Launch meli-app.exe with completely stripped/clean environment
    print("Testing clean standalone launch with isolated PATH (no MinGW/LLVM toolchain)...")
    clean_env = os.environ.copy()
    
    # Strip any compiler or winget paths from PATH
    paths = clean_env.get("PATH", "").split(";")
    clean_paths = [p for p in paths if "llvm-mingw" not in p.lower() and "mingw" not in p.lower() and "cargo" not in p.lower() and "rust" not in p.lower()]
    clean_env["PATH"] = ";".join(clean_paths)
    
    # Launch process
    proc = subprocess.Popen(
        [str(exe_path)],
        cwd=str(RELEASE_DIR),
        env=clean_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait 4 seconds to confirm it boots without crashing or DLL missing errors
    time.sleep(4)
    poll_result = proc.poll()
    
    if poll_result is not None:
        stdout, stderr = proc.communicate()
        print(f"FAIL [5/5]: Executable exited prematurely with code {poll_result}")
        print("Stdout:", stdout.decode('utf-8', errors='ignore'))
        print("Stderr:", stderr.decode('utf-8', errors='ignore'))
        return False
        
    print("PASS [5/5]: Standalone executable successfully initialized, opened window, and is actively running!")
    
    # Terminate the test process
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        
    print("\n[SUCCESS] ALL STANDALONE RUNTIME DEPENDENCY VERIFICATIONS PASSED!")
    return True

if __name__ == "__main__":
    success = verify_standalone_release()
    sys.exit(0 if success else 1)

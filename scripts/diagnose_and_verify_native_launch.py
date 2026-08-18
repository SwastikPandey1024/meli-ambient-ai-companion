import os
import sys
import json
import time
import urllib.request
import subprocess

def test_diagnostics():
    print("=" * 60)
    print("MELI NATIVE TAURI LAUNCH DIAGNOSTIC SUITE")
    print("=" * 60)

    # 1. Check Backend Health on port 8000
    print("[1/5] Checking FastAPI Backend Health on http://127.0.0.1:8000/api/health...")
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"       -> Backend healthy: status={data.get('status')}")
    except Exception as e:
        print(f"       -> ERROR: Backend not reachable on 8000: {e}")
        return False

    # 2. Check Frontend Dev Server on port 5173
    print("[2/5] Checking Vite Dev Server on http://127.0.0.1:5173...")
    try:
        req = urllib.request.Request("http://127.0.0.1:5173/")
        with urllib.request.urlopen(req, timeout=3) as resp:
            html = resp.read().decode()
            if "id=\"root\"" in html or "Meli" in html:
                print("       -> Frontend dev server running and serving index.html")
            else:
                print("       -> WARNING: HTML returned but missing root container")
    except Exception as e:
        print(f"       -> ERROR: Frontend not reachable on 5173: {e}")
        return False

    # 3. Check Persisted Window State on Disk
    print("[3/5] Checking Persisted window_state.json...")
    appdata = os.environ.get("APPDATA", "")
    state_file = os.path.join(appdata, "com.meli.companion", "window_state.json")
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = json.load(f)
            print(f"       -> Persisted state verified: visible={state.get('visible')}, bounds=({state.get('x')}, {state.get('y')}, {state.get('width')}x{state.get('height')})")
            if not state.get("visible"):
                print("       -> WARNING: Window was saved as hidden! Overriding to visible=True...")
                state["visible"] = True
                with open(state_file, "w") as fw:
                    json.dump(state, fw, indent=2)
    else:
        print(f"       -> No persisted state file found at {state_file} (Tauri will create default).")

    # 4. Check 16 Performance PNG Assets
    print("[4/5] Checking 16 canonical performance PNGs...")
    state_assets = [
        "meli_idle.png", "meli_curious.png", "meli_happy.png",
        "meli_thinking.png", "meli_working.png", "meli_focused.png",
        "meli_sleepy.png", "meli_confused.png", "meli_surprised.png",
        "meli_error.png", "meli_complete.png", "meli_greeting.png"
    ]
    special_assets = [
        "meli_click_pet.png", "meli_hover.png", "meli_proximity.png",
        "meli_celebration.png"
    ]
    for asset in state_assets:
        p = os.path.join("public", "states", asset)
        if not os.path.exists(p):
            print(f"       -> ERROR: State asset missing: {asset}")
            return False
    for asset in special_assets:
        p = os.path.join("public", "special", asset)
        if not os.path.exists(p):
            print(f"       -> ERROR: Special asset missing: {asset}")
            return False
    print("       -> All 16 assets verified on disk.")

    # 5. Check Native Rust Target Compilation
    print("[5/5] Checking native Cargo compilation...")
    res = subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "scripts/cargo_wrapper.ps1", "check"], capture_output=True, text=True)
    if res.returncode == 0:
        print("       -> Cargo check passed cleanly (0 errors).")
    else:
        print(f"       -> Cargo check failed:\n{res.stderr}")
        return False

    print("\n" + "=" * 60)
    print("ALL NATIVE LAUNCH DIAGNOSTIC CHECKS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    if not test_diagnostics():
        sys.exit(1)

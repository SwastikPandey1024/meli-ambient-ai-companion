#!/usr/bin/env python3
"""
Upload standalone Windows release artifact to GitHub Releases
"""

import os
import sys
import json
import urllib.request
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    print("=== Meli GitHub Release Asset Publisher ===")
    
    # 1. Get token
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(input='protocol=https\nhost=github.com\n\n')
    token = None
    for line in stdout.splitlines():
        if line.startswith('password='):
            token = line.split('=', 1)[1].strip()
            break

    if not token:
        print("Error: Could not retrieve GitHub token.")
        sys.exit(1)

    # 2. Get Release ID for v1.0.0
    repo = 'SwastikPandey1024/meli-ambient-ai-companion'
    req = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/releases/tags/v1.0.0',
        headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Meli-Release-Uploader', 'Accept': 'application/vnd.github.v3+json'}
    )
    with urllib.request.urlopen(req) as resp:
        release_info = json.loads(resp.read().decode('utf-8'))

    release_id = release_info['id']
    print(f"Target Release ID: {release_id} ({release_info.get('name')})")

    # 3. Check existing assets and delete if replacing
    existing_assets = release_info.get('assets', [])
    asset_name = 'Meli-v1.0.0-windows-x64.zip'
    for a in existing_assets:
        if a['name'] == asset_name:
            print(f"Deleting existing asset ID {a['id']}...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/assets/{a['id']}",
                headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Meli-Release-Uploader', 'Accept': 'application/vnd.github.v3+json'},
                method='DELETE'
            )
            with urllib.request.urlopen(del_req) as del_resp:
                print("Deleted old asset.")

    # 4. Upload fresh asset
    zip_file = Path('release/Meli-v1.0.0-windows-x64.zip')
    if not zip_file.exists():
        print("Error: release zip does not exist!")
        sys.exit(1)

    file_data = zip_file.read_bytes()
    file_size = len(file_data)
    upload_url = f"https://uploads.github.com/repos/{repo}/releases/{release_id}/assets?name={asset_name}"
    print(f"Uploading {asset_name} ({file_size / (1024*1024):.2f} MB)...")

    up_req = urllib.request.Request(
        upload_url,
        data=file_data,
        headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': 'Meli-Release-Uploader',
            'Content-Type': 'application/zip',
            'Content-Length': str(file_size),
            'Accept': 'application/vnd.github.v3+json'
        },
        method='POST'
    )

    with urllib.request.urlopen(up_req) as up_resp:
        uploaded = json.loads(up_resp.read().decode('utf-8'))
        print("\n[SUCCESS] Asset successfully published to GitHub Release:")
        print(f" - ID: {uploaded.get('id')}")
        print(f" - Name: {uploaded.get('name')}")
        print(f" - Size: {uploaded.get('size')} bytes ({uploaded.get('size') / (1024*1024):.2f} MB)")
        print(f" - Download URL: {uploaded.get('browser_download_url')}")

if __name__ == "__main__":
    main()

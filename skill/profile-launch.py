#!/usr/bin/env python3
"""
profile-launch.py — Launch Chrome with dedicated media-x-posting-profile.

Windows constraint: --remote-debugging-port REQUIRES a non-default data directory.
So we MUST use --user-data-dir pointing to C:/Users/EMIS-07/media-x-posting-profile.

Chrome binary: C:/Program Files/Google/Chrome/Application/chrome.exe
CDP port: 9222 (dedicated for this profile; do NOT reuse other CDP ports)
"""

import os
import subprocess
import sys
import time

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\EMIS-07\media-x-posting-profile"
CDP_PORT = 9222
CDP_BASE = f"http://127.0.0.1:{CDP_PORT}"

def main():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    if not os.path.isfile(CHROME_BIN):
        print(f"ERROR: Chrome binary not found at {CHROME_BIN}")
        sys.exit(1)
    
    # Kill any existing Chrome instance using THIS profile (not Boss's Chrome)
    # Use wmic to find chrome.exe processes with this profile path
    try:
        result = subprocess.run(
            ["wmic", "process", "where", f"name='chrome.exe' and commandline LIKE '%{PROFILE_DIR}%'", "get", "processid"],
            capture_output=True, text=True, timeout=10
        )
        pids = []
        for line in result.stdout.strip().split("\n"):
            parts = line.strip().split()
            if parts and parts[0].isdigit():
                pids.append(parts[0])
        if pids:
            # Kill only these PIDs (this profile's Chrome)
            for pid in pids:
                subprocess.run(["taskkill", "/PID", pid, "/F", "/T"], capture_output=True)
            print(f"Killed existing Chrome instances with profile {PROFILE_DIR} (PIDs: {pids})")
            time.sleep(2)
    except Exception as e:
        print(f"Warning: could not check/kill existing profile Chrome: {e}")
    
    # Launch Chrome with dedicated profile + CDP port
    cmd = [
        CHROME_BIN,
        f"--user-data-dir={PROFILE_DIR}",
        f"--remote-debugging-port={CDP_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-default-apps",
    ]
    
    print(f"Launching Chrome with profile: {PROFILE_DIR}")
    print(f"CDP port: {CDP_PORT}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f"Chrome PID: {proc.pid}")
    except Exception as e:
        print(f"ERROR launching Chrome: {e}")
        sys.exit(1)
    
    # Wait for CDP to become available
    print("Waiting for CDP port to be ready...")
    for i in range(30):
        time.sleep(1)
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"{CDP_BASE}/json/version", timeout=2)
            data = resp.read().decode("utf-8", errors="replace")
            if "Profile Path" in data and PROFILE_DIR in data:
                print(f"✓ Chrome launched with profile. CDP ready at {CDP_BASE}")
                print(f"Profile Path confirmed in CDP response.")
                return 0
            elif "Profile Path" in data:
                print("✓ Chrome launched but Profile Path doesn't match — possible wrong profile")
                print(data[:500])
            else:
                print(f"Attempt {i+1}: CDP responding but no Profile Path yet...")
        except Exception as e:
            print(f"Attempt {i+1}: CDP not ready ({e})")
    
    print("WARNING: CDP did not confirm profile path within 30s. Chrome may have launched with wrong profile.")
    print("Check manually: open Chrome and verify you're in media-x-posting-profile.")
    return 1

if __name__ == "__main__":
    sys.exit(main())

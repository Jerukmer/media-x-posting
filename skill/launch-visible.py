#!/usr/bin/env python3
"""
launch-visible.py — Kill existing headless Chrome on media-x-posting-profile,
then relaunch with visible window + CDP port 9222.

This lets Boss interact with Chrome directly to log into X.
"""

import os
import subprocess
import sys
import time

CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\EMIS-07\media-x-posting-profile"
CDP_PORT = 9222
CDP_BASE = f"http://127.0.0.1:{CDP_PORT}"

def find_and_kill_profile_chrome():
    """Find chrome.exe processes using our profile dir and kill them."""
    killed = []
    try:
        # Use wmic to find processes
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
            # Kill via taskkill (use subprocess with shell to avoid MSYS parsing issues)
            for pid in pids:
                try:
                    subprocess.run(
                        ["cmd", "/c", "taskkill", "/F", "/T", "/PID", pid],
                        capture_output=True, timeout=10
                    )
                    killed.append(pid)
                    print(f"Killed Chrome PID {pid}")
                except Exception as e:
                    print(f"Failed to kill PID {pid}: {e}")
            time.sleep(2)
    except Exception as e:
        print(f"Warning: wmic check failed: {e}")
    
    return killed

def launch_visible():
    """Launch Chrome visible with CDP port."""
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    if not os.path.isfile(CHROME_BIN):
        print(f"ERROR: Chrome binary not found at {CHROME_BIN}")
        sys.exit(1)
    
    # Launch Chrome VISIBLE (no CREATE_NO_WINDOW) with CDP port
    cmd = [
        CHROME_BIN,
        f"--user-data-dir={PROFILE_DIR}",
        f"--remote-debugging-port={CDP_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-default-apps",
    ]
    
    print(f"Launching VISIBLE Chrome with profile: {PROFILE_DIR}")
    print(f"CDP port: {CDP_PORT}")
    print()
    print("Chrome window should appear now — log into X (@penepian)")
    print("Once logged in, the session will persist in this profile.")
    print()
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Chrome PID: {proc.pid}")
        return proc
    except Exception as e:
        print(f"ERROR launching Chrome: {e}")
        sys.exit(1)

def wait_for_cdp(timeout=30):
    """Wait for CDP to be ready."""
    print("Waiting for CDP port to be ready...")
    for i in range(timeout):
        time.sleep(1)
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"{CDP_BASE}/json/version", timeout=2)
            data = resp.read().decode("utf-8", errors="replace")
            if "Browser" in data and "Chrome" in data:
                print(f"✓ CDP ready at {CDP_BASE}")
                return True
        except Exception:
            pass
        print(f"  Attempt {i+1}/{timeout}...", end="")
    print()
    print("⚠ CDP not confirmed within timeout — Chrome may still be launching")
    return False

def main():
    print("=== Killing existing headless Chrome on profile ===")
    killed = find_and_kill_profile_chrome()
    if not killed:
        print("No existing Chrome on this profile found (or already dead)")
    print()
    
    print("=== Launching visible Chrome ===")
    proc = launch_visible()
    
    print()
    wait_for_cdp()
    
    print()
    print("=== DONE ===")
    print("Chrome window should be visible now.")
    print("Log into @penepian via the Chrome window.")
    print("After login, run session-check.py to verify, then continue.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

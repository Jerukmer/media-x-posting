#!/usr/bin/env python3
"""
watchdog_once.py — Single watchdog check, exit immediately. Called by cron.
"""
import sys
import os
sys.path.insert(0, r"C:\Users\EMIS-07\media-x-posting")

from watchdog_cdp import check_once
check_once()

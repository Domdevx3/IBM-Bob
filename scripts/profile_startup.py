#!/usr/bin/env python3
"""
Startup Performance Profiler
Measures import times to identify bottlenecks
"""

import time
import sys

def time_import(module_name):
    """Time how long it takes to import a module"""
    start = time.time()
    try:
        __import__(module_name)
        elapsed = time.time() - start
        print(f"✓ {module_name:30s} {elapsed:6.3f}s")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ {module_name:30s} {elapsed:6.3f}s - {str(e)[:50]}")
        return elapsed

print("=" * 60)
print("STARTUP PERFORMANCE PROFILER")
print("=" * 60)
print()

total_time = 0

print("Core Python Libraries:")
print("-" * 60)
total_time += time_import("os")
total_time += time_import("sys")
total_time += time_import("json")
total_time += time_import("asyncio")
total_time += time_import("hashlib")
total_time += time_import("datetime")
total_time += time_import("typing")
total_time += time_import("functools")

print()
print("Third-Party Libraries:")
print("-" * 60)
total_time += time_import("dotenv")
total_time += time_import("requests")

print()
print("Heavy Libraries (Should be lazy-loaded):")
print("-" * 60)
total_time += time_import("flet")
total_time += time_import("PIL")

print()
print("Optional Heavy Libraries (Lazy-loaded):")
print("-" * 60)
print("⏭️  ibm_watsonx_ai (skipped - lazy loaded)")

print()
print("=" * 60)
print(f"TOTAL IMPORT TIME: {total_time:.3f}s")
print("=" * 60)
print()

# Now test actual app startup
print("Testing actual app startup...")
print("-" * 60)
start = time.time()

# Simulate app imports
import flet as ft
import os
import asyncio
import json
import hashlib
import requests
from functools import lru_cache
from dotenv import load_dotenv
from typing import Optional, Callable, List, Dict
from datetime import datetime

elapsed = time.time() - start
print(f"App imports completed in: {elapsed:.3f}s")
print()

if elapsed > 2.0:
    print("⚠️  WARNING: Startup is slow!")
    print("   Main bottleneck is likely Flet framework")
    print("   This is normal for Flet apps")
    print()
    print("Recommendations:")
    print("1. Use 'flet build' to create native app (faster)")
    print("2. Consider using --web flag for web version")
    print("3. Flet startup time is framework overhead")
else:
    print("✅ Startup time is acceptable!")

print()
print("=" * 60)

# Made with Bob

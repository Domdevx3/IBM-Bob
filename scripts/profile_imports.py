"""
Profile import times to identify slow startup bottlenecks
"""
import time
import sys

def time_import(module_name):
    """Time how long it takes to import a module"""
    start = time.time()
    try:
        __import__(module_name)
        elapsed = time.time() - start
        return elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, str(e)

print("=" * 60)
print("Import Time Profiler")
print("=" * 60)

modules_to_test = [
    'flet',
    'dotenv',
    'json',
    'hashlib',
    'requests',
    'asyncio',
    'threading',
    'functools',
    'datetime',
    'ibm_watsonx_ai',
    'PIL',
]

results = []
for module in modules_to_test:
    elapsed, error = time_import(module)
    status = "✅" if error is None else "❌"
    results.append((module, elapsed, status, error))
    if error:
        print(f"{status} {module:25s} {elapsed:6.3f}s - ERROR: {error}")
    else:
        print(f"{status} {module:25s} {elapsed:6.3f}s")

print("=" * 60)
print("Summary:")
print("=" * 60)

# Sort by time
results.sort(key=lambda x: x[1], reverse=True)
print("\nSlowest imports:")
for module, elapsed, status, error in results[:5]:
    if not error:
        print(f"  {module:25s} {elapsed:6.3f}s")

total_time = sum(r[1] for r in results if r[3] is None)
print(f"\nTotal import time: {total_time:.3f}s")
print("=" * 60)

# Made with Bob

import time
import sys
from pathlib import Path

log_file = Path('comprehensive_run.log')

print("=" * 80)
print("COMPREHENSIVE COMPARISON PROGRESS MONITOR")
print("=" * 80)
print("\nMonitoring: comprehensive_run.log")
print("Press Ctrl+C to stop monitoring\n")

last_position = 0
last_progress_line = None

try:
    while True:
        if log_file.exists():
            with open(log_file, 'r') as f:
                f.seek(last_position)
                new_content = f.read()
                last_position = f.tell()
                
                if new_content:
                    lines = new_content.strip().split('\n')
                    for line in lines:
                        # Look for progress lines
                        if '[' in line and ']' in line and 'routes' in line:
                            last_progress_line = line
                            print(f"\r{line}", end='', flush=True)
                        elif '✅' in line or 'Saved' in line or 'Complete' in line:
                            print(f"\n{line}")
                        elif 'Processing' in line or 'Testing' in line:
                            print(line)
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
    if last_progress_line:
        print(f"\nLast progress: {last_progress_line}")


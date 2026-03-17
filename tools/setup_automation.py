"""
setup_automation.py
-------------------
Detects OS and schedules run_pipeline.py to run at 6 AM and 8 PM daily.
On Windows, it also creates a Logon task for the 14-hour catch-up logic.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

def get_config():
    base_dir = Path(__file__).parent.parent.absolute()
    # Find python executable in .venv or fallback to current sys.executable
    venv_python = base_dir / ".venv" / "Scripts" / "python.exe" if platform.system() == "Windows" else base_dir / ".venv" / "bin" / "python"
    
    python_exe = str(venv_python) if venv_python.exists() else sys.executable
    script_path = str(base_dir / "tools" / "run_pipeline.py")
    
    return {
        "base_dir": str(base_dir),
        "python": python_exe,
        "script": script_path
    }

def setup_windows(config):
    print("Detected Windows. Setting up Task Scheduler...")
    
    tasks = [
        {"name": "Tweetify_Morning", "time": "06:00", "args": "--scheduled"},
        {"name": "Tweetify_Evening", "time": "20:00", "args": "--scheduled"},
        {"name": "Tweetify_Catchup", "trigger": "logon", "args": ""}
    ]
    
    for task in tasks:
        name = task["name"]
        command = f'"{config["python"]}" "{config["script"]}" {task["args"]}'.strip()
        
        # Delete existing if any
        subprocess.run(["schtasks", "/Delete", "/TN", name, "/F"], capture_output=True)
        
        if "time" in task:
            # Create daily task
            cmd = [
                "schtasks", "/Create", "/SC", "DAILY", "/TN", name, 
                "/TR", command, "/ST", task["time"], "/F"
            ]
        else:
            # Create logon task
            cmd = [
                "schtasks", "/Create", "/SC", "ONLOGON", "/TN", name, 
                "/TR", command, "/F"
            ]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  [OK] Scheduled {name}")
        else:
            print(f"  [ERROR] Failed to schedule {name}: {result.stderr.strip()}")

def setup_linux(config):
    print("Detected Linux/Unix. Please add the following to your crontab (crontab -e):")
    print(f"\n# Tweetify Morning Run\n0 6 * * * {config['python']} {config['script']} --scheduled")
    print(f"\n# Tweetify Evening Run\n0 20 * * * {config['python']} {config['script']} --scheduled")
    print(f"\n# Note: To enable catch-up on login, add the following to your .bashrc or .profile:")
    print(f"{config['python']} {config['script']}")

def main():
    config = get_config()
    os_name = platform.system()
    
    if os_name == "Windows":
        setup_windows(config)
    elif os_name in ["Linux", "Darwin"]:
        setup_linux(config)
    else:
        print(f"Unsupported OS: {os_name}")

    print("\nSetup complete. You can verify logs at .tmp/pipeline.log.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()

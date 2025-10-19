#!/usr/bin/env python3
"""
Setup script for RFToolkit
"""

import os
import sys
import subprocess
from pathlib import Path
# Checks for needed stuff:
def check_dependencies():
    """Check if required tools are installed"""
    required_tools = {
        'hackrf': 'hackrf_info',
        'git': 'git',
        'make': 'make', 
        'gcc': 'gcc',
        'cmake': 'cmake'
    }
    
    print("Checking dependencies...")
    all_found = True
    
    for tool_name, tool_cmd in required_tools.items():
        try:
            if tool_name == 'hackrf':
                result = subprocess.run([tool_cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("[OK] hackrf found")
                else:
                    print("[ERROR] hackrf not found or not working")
                    all_found = False
            else:
                subprocess.run([tool_cmd, '--version'], capture_output=True, check=True)
                print(f"[OK] {tool_name} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ERROR] {tool_name} not found")
            all_found = False
    
# Check for GPS spoofer shit
    print("Checking for GPS simulator dependencies...")
    gps_deps = ['bison', 'flex', 'doxygen']
    for dep in gps_deps:
        try:
            subprocess.run([dep, '--version'], capture_output=True, check=True)
            print(f"[OK] {dep} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[WARNING] {dep} not found (needed for GPS spoofing)")
    
    return all_found

def install_rf_toolkit():
    """Install the RF Toolkit"""
    print("Installing RF Toolkit...")
    
# mkdirs to create needed directories
    home_dir = Path.home()
    toolkit_dir = home_dir / ".rf_toolkit"
    toolkit_dir.mkdir(exist_ok=True)
    
# validate main script's existence
    main_script = Path("rftoolkit.py")
    if main_script.exists():
        main_script.chmod(0o755)
        print("[OK] Main script configured")
    else:
        print("[ERROR] Main script not found!")
        return False
    
    print("\nInstallation completed!")
    print("You can now run: python rftoolkit.py")
    print("Or: ./rftoolkit.py")
    return True

if __name__ == "__main__":
    print("RF Toolkit Setup")
    print("================")
# spoonfeed user with what stuff is missing    
    if check_dependencies():
        if install_rf_toolkit():
            print("\nSetup completed successfully!")
        else:
            print("\nSetup failed!")
            sys.exit(1)
    else:
        print("\nPlease install missing dependencies first!")
        print("try: sudo apt install hackrf gcc git make cmake")
        print("For GPS spoofing also install: libxml2 libxml2-dev bison flex libcdk5-dev libaio-dev libusb-1.0-0-dev libserialport-dev libavahi-client-dev doxygen graphviz")
        sys.exit(1)

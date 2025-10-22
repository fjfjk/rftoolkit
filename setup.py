#!/usr/bin/env python3
"""
Setup script for RFToolkit
Please launch before using anything else in the framework(really, it only installs basic stuff,
gps spoof and protocols tab have their own setup options)
"""

import os
import sys
import subprocess
from pathlib import Path

# Check what the fuck is the user running this on
def platform_check():
    #Check if we're on a supported platform
    print("Checking platform...")
    
    if sys.platform == "win32":
        print("[ERROR] Windows is not supported. Use WSL or a Linux VM.")
        print("This framework requires direct hardware access to HackRF.")
        return False
    elif sys.platform == "darwin":
        print("[ERROR] macOS is not officially supported.")
        print("You might be able to compile everything manually, but good luck with that.")
        return False
    elif sys.platform == "linux":
        print("[OK] Linux detected - supported platform")
        return True
    else:
        print("[ERROR] the fuck is happening - unknown platform")
        print(f"Detected platform: {sys.platform}")
        return False

# Checks for needed stuff:
def check_dependencies():
    required_tools = {
        'git': 'git',
        'make': 'make', 
        'gcc': 'gcc',
        'cmake': 'cmake'
    }
    
    print("Checking dependencies...")
    all_found = True
    
    # First check if hackrf package is installed
    print("Checking for HackRF...")
    hackrf_found = False
    
    # check if hackrf package is installed via dpkg
    try:
        result = subprocess.run(['dpkg', '-l', 'hackrf'], capture_output=True, text=True)
        if result.returncode == 0 and 'hackrf' in result.stdout:
            print("[OK] hackrf package installed")
            hackrf_found = True
        else:
            print("[INFO] hackrf package not found in dpkg")
    except:
        print("[INFO] Could not check dpkg for hackrf")
    
    #second hackrf check in PATH
    if not hackrf_found:
        try:
            result = subprocess.run(['which', 'hackrf_info'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] hackrf tools found in PATH")
                hackrf_found = True
        except:
            pass
    
    # third check by trying to run hackrf_info
    if not hackrf_found:
        try:
            result = subprocess.run(['hackrf_info', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] hackrf_info works")
                hackrf_found = True
        except:
            pass
    
    if not hackrf_found:
        print("[ERROR] HackRF not found! This is required for the framework.")
        print("Install it with: sudo apt install hackrf")
        all_found = False
    else:
        print("[OK] HackRF detected")
    
    # checking for other deps
    for tool_name, tool_cmd in required_tools.items():
        try:
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
    
    # Check for ADS-B dependencies
    print("Checking for ADS-B monitoring dependencies...")
    adsb_deps = ['librtlsdr-dev', 'pkg-config']
    for dep in adsb_deps:
        try:
            # Try to find the package
            result = subprocess.run(['dpkg', '-l', dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {dep} found")
            else:
                print(f"[INFO] {dep} not installed (needed for ADS-B monitoring)")
        except:
            print(f"[INFO] {dep} status unknown")
    
    # Check if readsb is available
    print("Checking for readsb...")
    try:
        result = subprocess.run(['which', 'readsb'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] readsb found")
        else:
            print("[INFO] readsb not found (will be installed when needed)")
    except:
        print("[INFO] readsb status unknown")
    
    return all_found

def install_rf_toolkit():
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
    
    # First check if we're on a supported platform
    if not platform_check():
        print("\nUnsupported platform detected!")
        sys.exit(1)
    
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
        print("For ADS-B monitoring also install: librtlsdr-dev pkg-config")
        print("Note: readsb will can be installed using a setup option in Protocols tab")
        sys.exit(1)

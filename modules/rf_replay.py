import os
import signal
import threading
import time
from pathlib import Path
import numpy as np
import subprocess
#defining stuff
class RFReplay:
    def __init__(self):
        self.recording = False
        self.base_dir = Path.home() / ".rf_toolkit" / "recordings"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self):
        while True:
# cool ass logo for the looks (coloring needed, it sucks D:)
            os.system('clear')
            print("======================================")
            print("            RF REPLAY MENU            ")
            print("======================================")
            print("1. Record RF Signal")
            print("2. Replay Recorded Signal")
            print("3. List Recordings")
            print("4. Back to Main Menu")
# choice for the options
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                self.record_signal()
            elif choice == '2':
                self.replay_signal()
            elif choice == '3':
                self.list_recordings()
            elif choice == '4':
                return
# hey! i didnt even forget to add some error handling, how nice of me ^_^
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    # stuff for signal recording
    def record_signal(self):
        try:
            freq = input("Enter frequency in MHz (e.g., 433.92): ").strip()
            if not freq.replace('.', '').isdigit():
                print("Invalid frequency!")
                return
            
            filename = input("Enter filename (without extension): ").strip()
            if not filename:
                filename = f"recording_{int(time.time())}"
            
            filepath = self.base_dir / f"{filename}.iq"
            
            print(f"\nRecording on {freq} MHz...")
            print("Press Ctrl+C to stop recording")
            
# using hackrf_transfer to do stuff, because its the easiest way to do everything, even tho only hackrf one is the only sdr supported that way:/
            cmd = [
                'hackrf_transfer', '-r', str(filepath),
                '-f', f"{float(freq)*1e6}", '-s', '2000000', '-g', '20', '-l', '32'
            ]
            
            process = subprocess.Popen(cmd)
            
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                print("\nRecording stopped!")
#MORE SLEEPS, YEEEEEEES, WASTE MORE OF USER'S PRECIOUS TIME
                time.sleep(1)
                # error handling because im nice :D
        except Exception as e:
            print(f"Recording error: {e}")
        input("Press Enter to continue...")
    # the replaying itself
    def replay_signal(self):
        recordings = list(self.base_dir.glob("*.iq"))
        if not recordings:
            print("No recordings found!")
            input("Press Enter to continue...")
            return
        
        print("\nAvailable recordings:")
        for i, rec in enumerate(recordings):
            print(f"{i+1}. {rec.name}")
        
        try:
            choice = int(input("\nSelect recording to replay: ")) - 1
            if 0 <= choice < len(recordings):
                freq = input("Enter replay frequency in MHz: ").strip()
                gain = input("Enter TX gain (0-47, default 20): ").strip() or "20"
                repeat = input("Repeat transmission? (y/n, default n): ").strip().lower() or "n"
                
                print(f"Replaying {recordings[choice].name} on {freq} MHz...")
                
                cmd = [
                    'hackrf_transfer', '-t', str(recordings[choice]),
                    '-f', f"{float(freq)*1e6}", 
                    '-s', '2000000', 
                    '-x', gain
                ]
                
                # Adding repeat option if requested (stupid ass thing, but oh well)
                if repeat == 'y':
                    cmd.append('-R')
                    print("Mode: Continuous repeat - Press Ctrl+C to stop")
                else:
                    print("Mode: Single transmission - Will stop automatically")
                
                # i didnt even know this existed :^)
                process = subprocess.Popen(cmd)
                
                try:
                    process.wait()
                except KeyboardInterrupt:
                    if repeat == 'y':
                        print("\nStopping repeated transmission...")
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                
            else:
                print("Invalid selection!")
        except (ValueError, KeyboardInterrupt):
            print("Operation cancelled!")
        
        input("Press Enter to continue...")
    # list of all recordings saved
    def list_recordings(self):
        recordings = list(self.base_dir.glob("*.iq"))
        if not recordings:
            print("No recordings found!")
        else:
            print("\nRecorded files:")
            for rec in recordings:
                size = rec.stat().st_size / (1024*1024)  # size in MB
                print(f"  {rec.name} ({size:.2f} MB)")
        
        input("\nPress Enter to continue...")

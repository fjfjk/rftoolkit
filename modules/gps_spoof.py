import os
import subprocess
from pathlib import Path
import time
import sys
import datetime
# Note before starting - i have no idea if this even works nowadays, and it will suck if it doesnt:D
class GPSSpoof:
    def __init__(self):
        self.gps_sim_dir = Path.home() / ".rf_toolkit" / "gps_sdr_sim"
        self.gps_sim_dir.mkdir(parents=True, exist_ok=True)
    
# hey - another cool menu ^_^
    def run(self):
        while True:
            os.system('clear')
            print("========================================")
            print("            GPS SPOOFING")
            print("========================================")
            print("1. Setup GPS SDR Simulator (First Time)")
            print("2. Generate GPS Signal")
            print("3. Real-time GPS Spoofing")
            print("4. Back to Main Menu")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                self.setup_gps_sdr_sim()
            elif choice == '2':
                self.generate_gps_signal()
            elif choice == '3':
                self.realtime_spoofing()
            elif choice == '4':
                return
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    # validate if the user set evertyhing up or give ligma
    # Edit: we dont give ligma, we tell to run setup
    def is_gps_sdr_sim_available(self):
        """Check if GPS SDR simulator is built and available"""
        gps_sdr_sim_path = self.gps_sim_dir / "gps-sdr-sim"
        return gps_sdr_sim_path.exists() and os.access(gps_sdr_sim_path, os.X_OK)
    # some other stuff, MORE EXISTENCE CHECKS
    def show_gps_data_instructions(self):
        """Show unified GPS data download instructions"""
        brdc_file = self.gps_sim_dir / "brdc.dat"
        today = datetime.datetime.now()
        doy = today.timetuple().tm_yday  # day of year(we need this, trust)
        year_short = today.strftime("%y")  # two-digit year(and this too) Edit: where tf did i need this?????
        # If user doesnt have ephemeris file:
        print("\n" + "="*50)
        print("GPS EPHEMERIS DATA REQUIRED")
        print("="*50)
        print("The GPS simulator needs current GPS broadcast ephemeris data.")
        print("\nDOWNLOAD INSTRUCTIONS:")
        print(f"1. Go to: https://cddis.nasa.gov/archive/gnss/data/daily/{datetime.datetime.now().year}/brdc/") #where i needed the year(the link changes every year)
        print("2. Create an account(you can use tempmail, but you really should update ephemeris from time to time, so not really needed)")
        print("3. Download the file named like: brdc{doy:03d}{year_short}n.gz (NOT the long once, scroll down to find the one you need)")
        print(f"   Example: brdc{doy:03d}{year_short}n.gz (for today)")
        print("4. Extract the compressed file:")
        print("   - Example: 'gunzip brdc{doy:03d}{year_short}n.gz'")
        print(f"5. Rename the file: 'mv brdc{doy:03d}{year_short}n {brdc_file}'")
        print(f"6. Final file should be: {brdc_file}")
        print("="*50)
    #set up the gps_sdr_sim (what we use to make a transmittable file to feed to sdr later)
    def setup_gps_sdr_sim(self):
        print("Setting up GPS SDR simulator...")
        print("This may take a few minutes...")
        
        try:
            # checks if already cloned(oh boy, did i learn the hard way)
            if (self.gps_sim_dir / ".git").exists():
                print("GPS SDR simulator already cloned. Pulling latest changes...")
                subprocess.run(['git', 'pull'], cwd=self.gps_sim_dir, check=True)
            else:
                # Clone the gps_sdr_sim repository from github
                print("Cloning GPS SDR simulator repository...")
                clone_cmd = [
                    'git', 'clone', 'https://github.com/osqzss/gps-sdr-sim.git',
                    str(self.gps_sim_dir)
                ]
                subprocess.run(clone_cmd, check=True)
            
            # build the gps_sim with GCC
	    # now gps_sdr_sim, im tupid
            print("Building GPS SDR simulator...")
            build_cmd = ['gcc', 'gpssim.c', '-lm', '-O3', '-o', 'gps-sdr-sim']
            result = subprocess.run(build_cmd, cwd=self.gps_sim_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("Build failed. Checking for common issues...")
                print(f"Build errors: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, build_cmd)
            
            # verify that the executable was created
            if self.is_gps_sdr_sim_available():
                print("GPS SDR simulator setup completed successfully!")
                print("Executable built: gps-sdr-sim")
                
                # Check if GPS data file exists in proper format and provide instructions if not
                brdc_file = self.gps_sim_dir / "brdc.dat"
                if not brdc_file.exists():
                    self.show_gps_data_instructions()
                    print("\n" + "="*50)
                    print("GPS EPHEMERIS DATA REQUIRED")
       	            print("="*50)
       	            print("The GPS simulator needs current GPS broadcast ephemeris data.")
       	            print("\nDOWNLOAD INSTRUCTIONS:")
                    print(f"1. Go to: https://cddis.nasa.gov/archive/gnss/data/daily/{datetime.datetime.now().year}/brdc/") #where i needed the year(the link changes every year)
                    print("2. Create an account(you can use tempmail, but you really should update ephemeris from time to time, so not really needed)")
       	            print("3. Download the file named like: brdc{doy:03d}{year_short}n.gz (NOT the long once, scroll down to find the one you need)")
       	            print(f"   Example: brdc{doy:03d}{year_short}n.gz (for today)")
       	            print("4. Extract the compressed file:")
                    print("   - Example: 'gunzip brdc{doy:03d}{year_short}n.gz'")
                    print(f"5. Rename the file: 'mv brdc{doy:03d}{year_short}n {brdc_file}'")
       	            print(f"6. Final file should be: {brdc_file}")
       	            print("="*50)
                    
            else:
# smth smth validation smth smth
                print("Build appeared successful but executable not found!")
                print("Looking for executable...")
                ls_result = subprocess.run(['ls', '-la'], cwd=self.gps_sim_dir, capture_output=True, text=True)
                print("Directory contents:")
                print(ls_result.stdout)
            # error handling!!!!
        except subprocess.CalledProcessError as e:
            print(f"Setup failed: {e}")
            print("\nYou may need to install GCC if not available:")
            print("sudo apt install gcc")
        except Exception as e:
            print(f"Error during setup: {e}")
        
        input("Press Enter to continue...")
#finally making the transmittable file
    def generate_gps_signal(self):
        if not self.is_gps_sdr_sim_available():
            print("GPS SDR simulator not found or not built! Run setup first.")
            print(f"Expected path: {self.gps_sim_dir / 'gps-sdr-sim'}")
            input("Press Enter to continue...")
            return
        
        try:
            # Check if GPS data file exists
            brdc_file = self.gps_sim_dir / "brdc.dat"
            if not brdc_file.exists():
                self.show_gps_data_instructions()
                input("Press Enter to continue...")
                return
            # setting coordinates | Edit: god fucking damn it i used multi_gps_sdr_sim, needed to re-write everything above D':
            print("Enter coordinates for GPS spoofing:")
            lat = input("Enter latitude (e.g., 40.7128 for NYC): ").strip()
            lon = input("Enter longitude (e.g., -74.0060 for NYC): ").strip()
            alt = input("Enter altitude in meters (default 100): ").strip() or "100"
            duration = input("Enter duration in seconds (default 300, max 86400): ").strip() or "300"
            
            # Create output filen
            output_file = self.gps_sim_dir / "gpssim.bin"
            
            # Generate GPS signal using gps-sdr-sim
            print("Generating GPS signal...")
            
            # Build the command using gps-sdr-sim
            # Format: gps-sdr-sim -e brdc.dat -l lat,lon,alt -d duration -b 8 , i made 10 iterations of this shit, idk how, idk why
            cmd = [
                './gps-sdr-sim',
                '-e', 'brdc.dat',
                '-l', f"{lat},{lon},{alt}",
                '-d', duration,
                '-b', '8'  # 8-bit samples for HackRF, how nice that i remembered that AFTER 8 TRIES
            ]
            
            print(f"Running: {' '.join(cmd)}")
            print("Output will be saved as: gpssim.bin")
            
            result = subprocess.run(cmd, cwd=self.gps_sim_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if the file was created (fr this time)
                default_output = self.gps_sim_dir / "gpssim.bin"
                if default_output.exists():
                    print(f"GPS signal generated successfully: {default_output}")
                    file_size = default_output.stat().st_size / (1024*1024)
                    print(f"File size: {file_size:.2f} MB")
                    print("You can now transmit this signal using option 3")
                else:
# error handling if some random bs happens somehow :/
                    print("Command succeeded but output file not found!")
                    print("Expected file: gpssim.bin")
            else:
                print(f"Error generating GPS signal (exit code: {result.returncode})")
                print(f"STDERR: {result.stderr}")
                print(f"STDOUT: {result.stdout}")
                print("\nIf automatic generation fails, try running manually:")
                print(f"cd {self.gps_sim_dir}")
                print(f"./gps-sdr-sim -e brdc.dat -l {lat},{lon},{alt} -d {duration} -b 8")
                print("# Output will be saved as gpssim.bin in the current directory")
            
        except Exception as e:
            print(f"Error generating GPS signal: {e}")
        
        input("Press Enter to continue...")
    # thingy that actually runs the spoof
    def realtime_spoofing(self):
        # Check for the default output file name
        gpssim_file = self.gps_sim_dir / "gpssim.bin"
        if not gpssim_file.exists():
            print("No GPS signal file found! Generate a signal first using option 2.")
            input("Press Enter to continue...")
            return
        
        try:
            freq = input("Enter transmission frequency in MHz (default 1575.42 for GPS L1): ").strip() or "1575.42"
            gain = input("Enter TX gain (0-47, default 20): ").strip() or "20"
            samp_rate = input("Enter sample rate in Hz (default 2600000): ").strip() or "2600000"
            repeat = input("Repeat transmission? (y/n, default y): ").strip().lower() or "y"
            
            print(f"\nTransmitting GPS signal on {freq} MHz...")
            print("GPS L1 frequency: 1575.42 MHz")
            print("Sample rate: {samp_rate} Hz")
            print("Press Ctrl+C to stop transmission")
            
            # transmission command for gps spoofing
            cmd = [
                'hackrf_transfer', '-t', 'gpssim.bin',
                '-f', f"{float(freq)*1e6}", 
                '-s', samp_rate,
                '-a', '1', '-x', gain
            ]
            
            # Adding repeat option if requested (stupid ass thing, but oh well)
            if repeat == 'y':
                cmd.append('-R')
                print("Mode: Continuous repeat")
            else:
                print("Mode: Single transmission")
            
            print(f"Command: {' '.join(cmd)}")
            print("Starting transmission in 3 seconds...")
            time.sleep(3)
            
            subprocess.run(cmd, cwd=self.gps_sim_dir)
            
        except KeyboardInterrupt:
            print("\nTransmission stopped by user!")
        except Exception as e:
            print(f"Error during transmission: {e}")
        
        input("Press Enter to continue...")

#holy shit thats a lot of imports, and at the time im doing this i have zero fucking idea what some of them do, lol
import os
import subprocess
import threading
import time
import json
from pathlib import Path
import datetime
import shutil
#some stuff
class Protocols:
    def __init__(self):
        self.base_dir = Path.home() / ".rf_toolkit" / "protocols"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.adsb_process = None
        self.monitoring = False
        self.aircraft_data = {}
        self.last_cleanup = time.time()
    #menu
    def run(self):
        while True:
            os.system('clear')
            print("========================================")
            print("             PROTOCOLS")
            print("========================================")
            print("1. ADS-B Aircraft Monitoring(BETA! Untested in environments with actual planes flying)")
            print("2. Back to Main Menu")
            print("More stuff will be added later")
            
            choice = input("\nEnter choice (1-2): ").strip()
            
            if choice == '1':
                self.adsb_menu()
            elif choice == '2':
                self.stop_adsb()
                return
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
#another menu thingy
    def adsb_menu(self):
        while True:
            os.system('clear')
            print("========================================")
            print("     ADS-B AIRCRAFT MONITORING(BETA)")
            print("========================================")
            print("1. Start ADS-B Monitoring")
            print("2. View Current Aircraft")
            print("3. Stop ADS-B Monitoring")
            print("4. Install readsb (First Time)")
            print("5. Back to Protocols Menu")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                self.start_adsb_monitoring()
            elif choice == '2':
                self.view_aircraft()
            elif choice == '3':
                self.stop_adsb()
            elif choice == '4':
                self.install_readsb()
            elif choice == '5':
                self.stop_adsb()
                return
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    
    def is_readsb_available(self):
        """Check if readsb is installed and available"""
        try:
            #check if it's in PATH
            result = subprocess.run(['which', 'readsb'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            
            #check common locations
            common_paths = [
                '/usr/bin/readsb',
                '/usr/local/bin/readsb',
                str(self.base_dir / 'readsb' / 'readsb'),
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    return True
                    
            return False
        except:
            return False
    
    def install_readsb(self):
        """Install readsb for ADS-B decoding"""
        print("Installing readsb for ADS-B monitoring...")
        
        #trying to install from repos
        print("Checking repositories...")
        try:
            #updating package list
            subprocess.run(['apt', 'update'], capture_output=True, check=True)
            
            #trying to install readsb
            print("Attempting to install readsb...")
            install_cmd = ['apt', 'install', '-y', 'readsb']
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Successfully installed readsb!")
                print("readsb is now available system-wide")
                return
            else:
                print("Could not install readsb, shit has happened:/")

        except subprocess.CalledProcessError as e:
            print(f"Repository installation failed: {e}")
        except Exception as e:
            print(f"Error during repository installation: {e}")
        
        #if repository installation fails, build from source
        print("Step 2: Building readsb from source...")
        try:
            readsb_dir = self.base_dir / "readsb"
            
            # remove existing directory if it exists
            if readsb_dir.exists():
                shutil.rmtree(readsb_dir)
            
            print("Cloning readsb repository...")
            clone_cmd = [
                'git', 'clone', 'https://github.com/wiedehopf/readsb.git',
                str(readsb_dir)
            ]
            subprocess.run(clone_cmd, check=True)
            
            print("Building readsb with HackRF support...")
            build_cmd = ['make', 'RTLSDR=yes']
            result = subprocess.run(build_cmd, cwd=readsb_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("readsb built successfully!")
                bin_path = readsb_dir / "readsb"
                if bin_path.exists():
                    print(f"Executable location: {bin_path}")
                    print("Note: This is a local build. For system-wide installation, run:")
                    print(f"sudo cp {bin_path} /usr/local/bin/")
            else:
                print("readsb build failed!")
                print(f"Build errors: {result.stderr}")
                print("\nYou may need to install build dependencies:")
                print("sudo apt install build-essential librtlsdr-dev pkg-config libusb-1.0-0-dev")
                #god fucking damn it im so tired of making error handling D:
        except Exception as e:
            print(f"Source build failed: {e}")
            print("\nAll installation methods failed.")
            print("Please install readsb manually:")
            print("sudo apt update && sudo apt install readsb")
        
        input("Press Enter to continue...")
    
    def get_readsb_path(self):
        """Get the path to readsb executable"""
        #checking system packages for readsb
        system_paths = [
            '/usr/bin/readsb',
            '/usr/local/bin/readsb',
        ]
        
        for path in system_paths:
            if Path(path).exists():
                return path
        
        # check the new local build
        local_path = str(self.base_dir / 'readsb' / 'readsb')
        if Path(local_path).exists():
            return local_path
        
        # last resort - check if it's in PATH somehow >:/
        try:
            result = subprocess.run(['which', 'readsb'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        return None
    #finally reached the beginning of the working part itself :'(
    def start_adsb_monitoring(self):
        """Start ADS-B monitoring with readsb"""
        if not self.is_readsb_available():
            print("readsb not found! Please install it first using option 4.")
            input("Press Enter to continue...")
            return
        
        readsb_path = self.get_readsb_path()
        if not readsb_path:
            print("Could not find readsb executable!")
            input("Press Enter to continue...")
            return
        
        try:
            # Stop any monitoring processes if they exist
            self.stop_adsb()
            
            print("Starting ADS-B monitoring with readsb...")
            print("Listening on 1090 MHz for aircraft transmissions")
            print("Using HackRF One as SDR device")
            print("HackRF RX LED should light up when monitoring starts")
            print("Press Ctrl+C in the aircraft view to stop monitoring")
            
            #command for readsb
            #EDIT: NOW with correct parameters
            cmd = [
                readsb_path,
                '--device-type', 'hackrf',
                '--gain', '20', #whoever didnt add shortages for keys is a fucking menace to society and needs to be shot >:( (joke(mb not))
                '--freq', '1090000000',
                '--net',
                '--net-json-port', '30005', # jesus christ, nice job, bruh
                '--stats-every', '10',
                '--lat', '0',
                '--lon', '0',
                '--interactive' # look at this fucking key
            ]
            
            print(f"Running: {' '.join(cmd)}")
            print("Starting...")
            time.sleep(1)
            
            self.monitoring = True
            self.adsb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            #start a thread to process output
            self.aircraft_data = {}
            monitor_thread = threading.Thread(target=self._process_adsb_output)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            #start another thread to monitor stderr for device status
            #NOTE: god im so fucking confused, what am i doing rn????
            error_thread = threading.Thread(target=self._monitor_errors)
            error_thread.daemon = True
            error_thread.start()
            
            print("ADS-B monitoring started successfully!")
            print("Switch to 'View Current Aircraft' to see detected planes")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error starting ADS-B monitoring: {e}")
            self.monitoring = False
        
        input("Press Enter to continue...")
    
    def _monitor_errors(self):
        """Monitor stderr for device status messages"""
        while self.monitoring and self.adsb_process:
            try:
                line = self.adsb_process.stderr.readline()
                if not line:
                    break
                
                #print any error messages if anything shitted itself in the process
                if line.strip():
                    print(f"readsb: {line.strip()}")
                    
            except Exception as e:
                break
    
    def _process_adsb_output(self):
        #process readsb interactive output in a separate thread(this is why we cant have nice things... except this framework:D)
        aircraft_section = False
        header_lines = 0
        
        while self.monitoring and self.adsb_process:
            try:
                line = self.adsb_process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                
                #reset state when we see the header
                if line.startswith('Hex'):
                    aircraft_section = True
                    header_lines = 0
                    continue
                
                #skip separator lines shitted out by the thingy
                if line.startswith('---'):
                    header_lines += 1
                    continue
                
                # FINALLY, we're in the aircraft data section after the header
                if aircraft_section and header_lines >= 1:
                    # Parse aircraft data line
                    self._parse_aircraft_line(line)
                    
            except Exception as e:
                # Continue processing even if one line fails SOMEHOW
                continue
    
    def _parse_aircraft_line(self, line):
        #parse a single aircraft data line from readsb interactive output
        try:
            # split it by spaces, but have fields that might have spaces
            parts = line.split()
            if len(parts) < 6:
                return
            
            # NOTE: the format is typically: Hex Mode Sqwk Flight Alt Spd Hdg Lat Long Sig Msgs Ti/
            # NOTE: look at me figuring out that i used all the wrong ones all this time:D
            hex_code = parts[0]
            
            # Validate hex code (6 characters, hexadecimal)
            if len(hex_code) != 6 or not all(c in '0123456789abcdefABCDEF' for c in hex_code):
                return
            
            aircraft_info = {}
            aircraft_info['hex'] = hex_code.upper()
            
            # Find the flight callsign - it's usually at position 3, but might be variable
            flight_index = 3
            if len(parts) > flight_index:
                flight = parts[flight_index]
                # flight callsign should be alphanumeric, if its not - fuck you
                if (flight not in ['N/A', '---', '?'] and 
                    not flight.replace('.', '').isdigit() and
                    not flight.startswith('-')):
                    aircraft_info['flight'] = flight
            
            # altitude is usually at position 4
            if len(parts) > 4:
                alt_str = parts[4]
                if alt_str not in ['N/A', '---', '?'] and not alt_str.startswith('-'):
                    try:
                        alt = int(alt_str)
                        aircraft_info['altitude'] = f"{alt} ft"
                    except ValueError:
                        pass
            
            # speed should go fifth
            if len(parts) > 5:
                speed_str = parts[5]
                if speed_str not in ['N/A', '---', '?'] and not speed_str.startswith('-'):
                    try:
                        speed = int(speed_str)
                        aircraft_info['speed'] = f"{speed} kts"
                    except ValueError:
                        pass
            
            # Heading should be sixth
            if len(parts) > 6:
                heading_str = parts[6]
                if heading_str not in ['N/A', '---', '?'] and not heading_str.startswith('-'):
                    try:
                        heading = int(heading_str)
                        aircraft_info['heading'] = f"{heading}°"
                    except ValueError:
                        pass
            
            # Update the timestamp
            aircraft_info['last_seen'] = datetime.datetime.now().strftime("%H:%M:%S")
            
            #only store if we have at least the hex code(or else wth do we do with that:/)
            if aircraft_info:
                self.aircraft_data[hex_code.upper()] = aircraft_info
                
        except Exception as e:
            # Skip parsing errors (because fuck ads b, ancient ahh protocol)
            pass
    
    def _cleanup_old_aircraft(self):
        """Remove aircraft that haven't been seen recently"""
        current_time = time.time()
        # Clean up this shit every 30 seconds
        if current_time - self.last_cleanup > 30:
            expired_hexes = []
            for hex_code, aircraft in self.aircraft_data.items():
                last_seen_str = aircraft.get('last_seen', '')
                try:
                    # Parse time in Hours:Minues:Seconds
                    last_seen_time = datetime.datetime.strptime(last_seen_str, "%H:%M:%S")
                    now = datetime.datetime.now()
                    #create comparable datetime objects
                    last_seen_dt = last_seen_time.replace(year=now.year, month=now.month, day=now.day)
                    time_diff = now - last_seen_dt
                    
                    #remove any aircraft older than 2 minutes
                    if time_diff.total_seconds() > 120:
                        expired_hexes.append(hex_code)
                except:
                    #remove the aircraft if the time thingy is fucked
                    expired_hexes.append(hex_code)
            
            for hex_code in expired_hexes:
                del self.aircraft_data[hex_code]
            
            self.last_cleanup = current_time
    
    def view_aircraft(self):
        #Displays current aircraft in a structured format(so pretty yet so ugly...)
        if not self.monitoring or not self.adsb_process:
            print("ADS-B monitoring is not running!")
            print("Start monitoring first using option 1.")
            input("Press Enter to continue...")
            return
        
        try:
            while True:
                #look at this beauty
                os.system('clear')
                print("========================================")
                print("        CURRENT AIRCRAFT - ADS-B")
                print("========================================")
                print(f"Last update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Clean up old aircraft before displaying
                self._cleanup_old_aircraft()
                
                print(f"Aircraft detected: {len(self.aircraft_data)}")
                print("="*60)
                
                if not self.aircraft_data:
                    print("No aircraft currently in range...")
                    print("")
                    print("Check RX LED on your hackrf, also make sure that your antenna supports the 1090 MHz frequency")
                else:
                    # LIKE IT, i spent too much time making this somewhat nice looking D:
                    print(f"{'Callsign':<9} {'Alt':<8} {'Speed':<8} {'Heading':<9} {'Last Seen':<9}")
                    print("-" * 60)
                    
                    # Sort aircraft by last seen (newest first)
                    sorted_aircraft = sorted(self.aircraft_data.values(), 
                                           key=lambda x: x.get('last_seen', ''), 
                                           reverse=True)
                    
                    for aircraft in sorted_aircraft[:30]:  # Show max 30 aircraft
                        callsign = aircraft.get('flight', aircraft.get('hex', 'N/A'))
                        altitude = aircraft.get('altitude', '---')
                        speed = aircraft.get('speed', '---')
                        heading = aircraft.get('heading', '---')
                        last_seen = aircraft.get('last_seen', '---')
                        
                        # Give the callsign israel men treatment if too long
                        if len(callsign) > 10:
                            callsign = callsign[:10]
                        
                        print(f"{callsign:<9} {altitude:<8} {speed:<8} {heading:<9} {last_seen:<9}")
                    
                    if len(self.aircraft_data) > 30:
                        print(f"... and {len(self.aircraft_data) - 30} more aircraft")
                
                print("\n" + "="*60)
                print("Press Ctrl+C to return to ADS-B menu")
                print("Listening on 1090 MHz - Updates every 3 seconds")
                
                #update every 3 seconds and expect user interrupt
                try:
                    time.sleep(3)
                except KeyboardInterrupt:
                    print("\nReturning to ADS-B menu...")
                    break
                    
        except KeyboardInterrupt:
            print("\nReturning to ADS-B menu...")
        except Exception as e:
            print(f"Error displaying aircraft: {e}")
            input("Press Enter to continue...")
    
    def stop_adsb(self):
        """Stop ADS-B monitoring"""
        self.monitoring = False
        
        if self.adsb_process:
            print("Stopping ADS-B monitoring...")
            self.adsb_process.terminate()
            
            try:
                self.adsb_process.wait(timeout=5)
                print("ADS-B monitoring stopped successfully!")
            except subprocess.TimeoutExpired:
                print("Force stopping ADS-B monitoring...")
                self.adsb_process.kill()
                self.adsb_process.wait()
            
            self.adsb_process = None
        
        # nuke any remaining readsb processes
        subprocess.run(['pkill', '-f', 'readsb'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        self.aircraft_data = {}
        self.last_cleanup = time.time()
    
    def __del__(self):
        # additional cleanup when object is destroyed
        self.stop_adsb()

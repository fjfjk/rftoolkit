#NOTE: i am re-writing this shit, because nothing fucken worked, and now i am kinda here, so:
import os
import subprocess
import threading
import time
import datetime
import shutil
import signal
import atexit
import json
import re
from pathlib import Path
from queue import Queue, Empty

class ADSB:
    #configuration and application state
    def __init__(self):
        #setup the base directories for configs and output... and stuff, iunno
        self.base_dir = Path.home() / ".rf_toolkit" / "protocols"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.base_dir / "adsb_config.json"
        
        #config init + load
        self._set_default_config()
        self._load_config()
        
        #vars for stuff
        self.adsb_process = None
        self.monitoring = False
        self.aircraft_data = {}
        self.last_cleanup = time.time()
        
        self.debug_mode = False
        self.raw_output_queue = Queue()     #queue to handle output transfer
        self.raw_output_buffer = []         #ngl, no idea what this is, figure it out yourself
        self.has_received_data = False      #confirm that the fucker is actually outputting data
        
        #cleanup function
        atexit.register(self._exit_cleanup)
    
    #defaults for the command
    def _set_default_config(self):
        self.config = {
            "gain": 20,                  #gain in dB (0 to 48)(the bigger the number, the higher the sensitivity, but the noise is also louder)
            "freq": 1090000000,          #ads-b frequency (1090 MHz), idk who will want to edit that, but oh well
            "lat": 0.0,                  #our latitude for CPR
            "lon": 0.0,                  #and our longitude for CPR
            "stats_every": 10            #how often does readsb prints statistics
        }

    # Saves the current configuration to a jason's son
    def _save_config(self):
        try:
            with self.config_path.open('w') as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    #loadd configuration from a file or save defaults if none exists
    def _load_config(self):
        try:
            with self.config_path.open('r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
        except Exception:
            self._save_config()
            
    #nuke subprocesses after exiting the script if some were left alive
    def _exit_cleanup(self):
        if self.monitoring or self.adsb_process:
            self.stop_adsb()
    
    #main menu
    def run(self):
        try:
            while True:
                os.system('clear')
                print("========================================")
                print("     ADS-B AIRCRAFT MONITORING")
                print("========================================")
                
                debug_status = "ON(raw data)" if self.debug_mode else "OFF"
                print(f"Debug Mode: {debug_status}")
                print("----------------------------------------")
                print("1. Start ADS-B Monitoring")
                print("2. View Current Aircraft Output")
                print("3. Stop ADS-B Monitoring")
                print("4. Install readsb")
                print("5. Configure HackRF Settings")
                print("6. Toggle Debug Mode")
                print("7. Back to Protocols Menu")
                
                choice = input("\nEnter choice (1-7): ").strip()
                
                if choice == '1':
                    self.start_adsb_monitoring()
                elif choice == '2':
                    self.view_aircraft()
                elif choice == '3':
                    self.stop_adsb()
                elif choice == '4':
                    self.install_readsb()
                elif choice == '5':
                    self.configure_settings()
                elif choice == '6':
                    self.debug_mode = not self.debug_mode
                    print(f"Debug Mode set to {'ON' if self.debug_mode else 'OFF'}.")
                    input("Press Enter to continue...")
                elif choice == '7':
                    self.stop_adsb()
                    return
                else:
                    print("Invalid choice!")
                    input("Press Enter to continue...")
        except KeyboardInterrupt:
            self.stop_adsb()
            return
    
    # Checks if the readsb exists
    def is_readsb_available(self):
        try:
            # Check system path
            if subprocess.run(['which', 'readsb'], capture_output=True, text=True).returncode == 0:
                return True
            
            # Check local build path
            if (self.base_dir / 'readsb' / 'readsb').exists():
                return True
                    
            return False
        except:
            return False
    
    #install the readsb via apt or source
    def install_readsb(self):
        print("Installing readsb...")
        
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True)
            install_cmd = ['sudo', 'apt', 'install', '-y', 'readsb']
            subprocess.run(install_cmd, check=True, capture_output=True, text=True)
            
            print("Successfully installed readsb from repositories!")
            return
        except subprocess.CalledProcessError:
            print("System package installation failed. Proceeding to source build...")
        except Exception as e:
            print(f"Error during repository check: {e}")

        try:
            readsb_dir = self.base_dir / "readsb"
            if readsb_dir.exists():
                shutil.rmtree(readsb_dir)
            
            print("Cloning readsb repository...")
            subprocess.run(['git', 'clone', 'https://github.com/wiedehopf/readsb.git', str(readsb_dir)], check=True)
            
            print("Building readsb...")
            # Use RTLSDR=yes build option, cause shit may happen otherwise
            build_cmd = ['make', 'RTLSDR=yes']
            subprocess.run(build_cmd, cwd=readsb_dir, check=True, capture_output=True, text=True)
            
            print("readsb built successfully locally!")
        except subprocess.CalledProcessError as e:
            print("readsb source build failed.")
            print(f"Errors:\n{e.stderr}")
        except Exception as e:
            print(f"Source build failed: {e}")
            
        input("Press Enter to continue...")
    
    # Returns the full path to the readsb executable
    def get_readsb_path(self):
        local_path = str(self.base_dir / 'readsb' / 'readsb')
        if Path(local_path).exists():
            return local_path
        
        try:
            result = subprocess.run(['which', 'readsb'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        return None
        
    # change config
    def configure_settings(self):
        os.system('clear')
        print("========================================")
        print("      CONFIGURE ADS-B SETTINGS")
        print("========================================")
        print(f"Current HackRF Gain (dB): {self.config['gain']}")
        print(f"Current Frequency (hz): {self.config['freq']}")
        print(f"Current Latitude: {self.config['lat']}")
        print(f"Current Longitude: {self.config['lon']}")
        print("----------------------------------------")

        try:
            gain = input(f"Enter HackRF Gain (dB, e.g., 0-48) [Current: {self.config['gain']}]: ")
            if gain:
                self.config['gain'] = int(gain)

            freq = input(f"Enter Frequency (hz, default 1090000000) [Current: {self.config['freq']}]: ")
            if freq:
                self.config['freq'] = int(freq)

            lat = input(f"Enter Receiver Latitude (e.g., 34.05) [Current: {self.config['lat']}]: ")
            if lat:
                self.config['lat'] = float(lat)

            lon = input(f"Enter Receiver Longitude (e.g., -118.24) [Current: {self.config['lon']}]: ")
            if lon:
                self.config['lon'] = float(lon)

            self._save_config()
            print("\nSettings saved successfully.")

        except ValueError:
            print("\nInvalid input. Settings not saved. Please enter numeric values.") #fuck this word is weird
        except Exception as e:
            print(f"\nAn error occurred: {e}")

        input("Press Enter to continue...")
    
    #start readsb subprocess
    def start_adsb_monitoring(self):
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
            self.stop_adsb()
            
            print("Starting ADS-B monitoring...")
            
            #readsb launch command.... NOW with correct parameters(trust) NOTE: if you dont know - this is a 4-th iteration bc shit didnt want to work
            cmd = [
                readsb_path,
                '--device-type', 'hackrf',
                '--gain', str(self.config['gain']),
                '--freq', str(self.config['freq']),
                '--lat', str(self.config['lat']),
                '--lon', str(self.config['lon']),
                '--stats-every', str(self.config['stats_every']),
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            self.monitoring = True
            self.aircraft_data = {}
            self.raw_output_buffer = []
            self.has_received_data = False
            
            #subprocess that captures stdout and stderr
            self.adsb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                preexec_fn=os.setsid #process group for easy shutdown
            )
            
            #threads to read subprocess output(not united bc stuff kept breaking)
            threading.Thread(target=self._enqueue_output, daemon=True).start()
            threading.Thread(target=self._process_data, daemon=True).start()
            
            print("ADS-B monitoring process initiated. Data will be available shortly.")
            time.sleep(2)
            
        except Exception as e:
            print(f"\n[!] Error starting ADS-B monitoring: {e}")

            #try to show stderr output if the process started partially
            if self.adsb_process and self.adsb_process.stderr:
                try:
                    #read any stderr output
                    err_output = self.adsb_process.stderr.read().strip()
                    if err_output:
                        print("\n--- readsb stderr output ---")
                        print(err_output)
                        print("--- end of stderr ---\n")
                except Exception as err_read:
                    print(f"(Could not read stderr: {err_read})")

            #check for if readsb binary exists
            readsb_path_test = self.get_readsb_path()
            if not readsb_path_test or not os.access(readsb_path_test, os.X_OK):
                print(f"readsb not found or not executable at: {readsb_path_test or 'None'}")
                print("\nTry reinstalling via menu option 4 (Install readsb).")

            print("Monitoring not started.")
            self.monitoring = False
        
        input("Press Enter to continue...")


    
    #thread function to read from subprocess pipe and put the lines into a queue
    def _enqueue_output(self):
        def read_pipe(pipe, source):
            while self.monitoring:
                try:
                    line = pipe.readline()
                    if line:
                        self.raw_output_queue.put(line)
                    else:
                        #check if shit has happened
                        if self.adsb_process.poll() is not None:
                            break
                        time.sleep(0.1)
                except Exception:
                    break

        if self.adsb_process and self.adsb_process.stdout:
            threading.Thread(target=read_pipe, args=(self.adsb_process.stdout, 'stdout'), daemon=True).start()
        if self.adsb_process and self.adsb_process.stderr:
            threading.Thread(target=read_pipe, args=(self.adsb_process.stderr, 'stderr'), daemon=True).start()

    #process the queue data
    def _process_data(self):
        while self.monitoring:
            try:
                #read from queue EDIT: now without blocking
                line = self.raw_output_queue.get_nowait()
                line_str = line.strip()
                
                if not line_str:
                    continue
                
                # Set data received flag if any non-empty line is seen
                if not self.has_received_data and len(line_str) > 5:
                    self.has_received_data = True

                #raw output buffer for debug view
                self.raw_output_buffer.append(line_str)
                
                # keep buffer manageable
                if len(self.raw_output_buffer) > 200: 
                    self.raw_output_buffer = self.raw_output_buffer[-100:]

                #raw Mode-S message parsing for table view (only when debug is off) NOTE: more stuff needs to be added, but this will do for now
                if not self.debug_mode and line_str.startswith('*') and line_str.endswith(';'):
                    self._parse_raw_line(line_str)

                # better error/warning handling, because Of Course I'm The One, you moron! I am The Son of GOD!! I was sent down by my father, to lead his flock to paradise... To atone for the sins of Adam and Eve in the garden! I am of one flesh with the divine, and of the lineage of Abraham! I will bring forth a new age, and a new covenant, shall be my legacy! I WILL VANQUISH, ALL EVIL, IN MY FATHER'S NAME! AMEN!!!
                is_stat_line_type_a = any(stat in line_str for stat in ['samples processed', 'Mode-S message preambles received', 'CPU load:'])
                is_stat_line_type_b = any(stat in line_str.lower() for stat in ['accepted with', 'cpr messages', 'local cpr attempts'])
                
                # ONLY flag as error if it's not a statistical line AND contains an error keyword
                if not is_stat_line_type_a and not is_stat_line_type_b and any(err in line_str.lower() for err in ['fail', 'fatal', 'error', 'cannot open', 'device not found']):
                    print(f"\n!!! READSB ERROR: {line_str}")
                    
            except Empty:
                time.sleep(0.1) # Wait if queue is empty
            except Exception:
                pass

    #simple parse function to extract ICAO address
    def _parse_raw_line(self, line):
        try:
            # Regex to match the raw message format NOTE: this shit is so fucking confusing
            match = re.match(r'\*([0-9a-fA-F]{14,28});', line)
            if not match:
                return

            full_hex_payload = match.group(1)
            icao_address = None
            
            #fallback parsing ICAO is the 3rd to 8th hex character of the message payload
            # Made for DF17 (Extended Squitter... or sm shit) bc ads-b is dum
            if len(full_hex_payload) >= 8:
                icao_address = full_hex_payload[2:8].upper()
            
            if icao_address and len(icao_address) == 6:
                #add the aircraft data table with the hex code and current time
                self.aircraft_data[icao_address] = {
                    'hex': icao_address,
                    'last_seen': datetime.datetime.now().strftime("%H:%M:%S")
                }
                
        except Exception:
            pass
    
    # Removes aircraft from the list if they haven't been seen in the last 120 seconds
    def _cleanup_old_aircraft(self):
        current_time = time.time()
        
        if current_time - self.last_cleanup > 30:
            expired_hexes = []
            
            for hex_code, aircraft in list(self.aircraft_data.items()):
                last_seen_str = aircraft.get('last_seen')
                if not last_seen_str:
                    expired_hexes.append(hex_code)
                    continue

                try:
                    last_seen_time = datetime.datetime.strptime(last_seen_str, "%H:%M:%S")
                    now = datetime.datetime.now()
                    # handle time wrap around midnight by checking if last_seen is future
                    last_seen_dt = last_seen_time.replace(year=now.year, month=now.month, day=now.day)
                    if last_seen_dt > now:
                        last_seen_dt = last_seen_dt - datetime.timedelta(days=1)
                        
                    time_diff = now - last_seen_dt
                    
                    if time_diff.total_seconds() > 120: # 2 minutes timeout
                        expired_hexes.append(hex_code)
                except ValueError:
                    expired_hexes.append(hex_code)

            for hex_code in expired_hexes:
                self.aircraft_data.pop(hex_code, None)
            
            self.last_cleanup = current_time

    #the main output display(raw or parsed)
    def view_aircraft(self):
        if not self.monitoring or not self.adsb_process:
            print("ADS-B monitoring is not running! Start monitoring first using option 1.")
            input("Press Enter to continue...")
            return
        
        try:
            while True:
                os.system('clear')
                print("========================================")
                print("        AIRCRAFT DATA - ADS-B")
                print("========================================")
                print(f"Last Update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Mode: {'RAW DATA (DEBUG)' if self.debug_mode else 'DECODED DATA'}")
                print("="*50)
                
                #status output
                if self.has_received_data:
                    print("Monitoring is active: data (setup messages, raw input, or stats) is being received.")
                else:
                    print("Monitoring started, but no output data has been captured yet. Check HackRF connection and ensure readsb is running.")
                print("="*50)

                if self.debug_mode:
                    #raw data ou- okay, its literally said below, common now, you dont need this comment
                    print("--- RAW READSB OUTPUT ---")
                    
                    if self.raw_output_buffer:
                        for line in self.raw_output_buffer[-50:]:
                            print(line)
                    else:
                        print("No raw data buffer available yet.")
                    
                else:
                    # decoded ICAO view (Simple ICAO list)
                    self._cleanup_old_aircraft()
                    
                    print(f"Aircraft tracks seen (Last 2 minutes): {len(self.aircraft_data)}")
                    print("="*50)
                    
                    if not self.aircraft_data:
                        print("No aircraft tracks currently active. The table view requires decoded Mode-S messages.")
                    else:
                        
                        print(f"{'ICAO Hex':<10} {'Last Seen':<9}")
                        print("-" * 19)
                        
                        sorted_aircraft = sorted(self.aircraft_data.values(), 
                                               key=lambda x: x.get('last_seen', ''), 
                                               reverse=True)
                        
                        for aircraft in sorted_aircraft[:30]:
                            hex_code = aircraft.get('hex', '---')
                            last_seen = aircraft.get('last_seen', '---')
                            
                            print(f"{hex_code:<10} {last_seen:<9}")
                        
                        if len(self.aircraft_data) > 30:
                            print(f"... and {len(self.aircraft_data) - 30} more tracks")
                
                print("\n" + "="*50)
                print("Press Ctrl+C to return to ADS-B menu")
                print("Monitoring continues running in background")
                
                try:
                    time.sleep(3) # update interval
                except KeyboardInterrupt:
                    time.sleep(1)
                    break
                    
        except KeyboardInterrupt:
            time.sleep(1)
        except Exception as e:
            print(f"Error displaying output: {e}")
            input("Press Enter to continue...")
    
    #stup readsb subprocess and cleanup
    def stop_adsb(self):
        if not self.monitoring and not self.adsb_process:
            return
        
        self.monitoring = False
        
        if self.adsb_process:
            print("Stopping ADS-B monitoring...")
            
            try:
                # Terminate the process group
                process_group_id = os.getpgid(self.adsb_process.pid)
                os.killpg(process_group_id, signal.SIGTERM)
                self.adsb_process.wait(timeout=5)
            except Exception:
                try:
                    # Force kill if suckers resist
                    os.killpg(process_group_id, signal.SIGKILL)
                    self.adsb_process.wait(timeout=2)
                except:
                    pass
            
            self.adsb_process = None
        
        # Fallback to kill any lingering readsb processes
        subprocess.run(['pkill', '-f', 'readsb'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Reset the state
        self.aircraft_data = {}
        self.raw_output_buffer = [] 
        self.last_cleanup = time.time()
        self.has_received_data = False
        
        time.sleep(1)

if __name__ == '__main__':
    adsb_tool = ADSB()
    adsb_tool.run()
#NOTE: THIS SHIT WORKS!!!! I JUST TESTED IT AND THERE IS OUTPUT, HOLY FUCK I AM FREEEEEEEEEEEEEEEEEEEEEEEEEEEEE

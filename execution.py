# execution.py
import os
import glob

# Confirmed MT5 Files path on Zorin OS (Wine)
PRIMARY_MQL5_DIR = "/home/sv/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files"

class ExecutionModule:
    def __init__(self):
        os.makedirs(PRIMARY_MQL5_DIR, exist_ok=True)
        print(f"Verified Execution Target Active: {PRIMARY_MQL5_DIR}")

    def route_order(self, symbol, action, decision_data, risk_percentage=1.0):
        command = f"{action}_{symbol}"
        
        target_dirs = [PRIMARY_MQL5_DIR]
        
        # Backup pattern check for AppData dynamic hashes
        appdata_pattern = os.path.expanduser("~/.wine/drive_c/users/*/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Files")
        target_dirs.extend(glob.glob(appdata_pattern))
        
        written_count = 0
        for target_dir in set(target_dirs):
            try:
                os.makedirs(target_dir, exist_ok=True)
                file_path = os.path.join(target_dir, "ai_hedge_fund_signal.txt")
                with open(file_path, "w") as f:
                    f.write(command)
                written_count += 1
            except Exception as e:
                print(f"Failed writing to {target_dir}: {e}")
                
        if written_count > 0:
            print(f"Success: Signal {command} safely written to raw path ({written_count} target location(s)).")
        else:
            print("Execution Route Error: Could not write signal file to target location.")
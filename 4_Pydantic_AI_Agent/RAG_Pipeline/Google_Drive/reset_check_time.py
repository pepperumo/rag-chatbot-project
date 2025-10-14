"""
Reset the last_check_time in config.json to force a full rescan of all files.
"""
import json
from pathlib import Path

# Get the directory where the script is located
script_dir = Path(__file__).resolve().parent
config_path = script_dir / 'config.json'

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Reset to a very old date to force scanning all files
    config['last_check_time'] = '1970-01-01T00:00:00.000000Z'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Successfully reset last_check_time to 1970-01-01T00:00:00.000000Z")
    print(f"   Updated config file: {config_path}")
    print("\nNow run 'python main.py' to perform a full scan of all files.")
    
except FileNotFoundError:
    print(f"❌ Config file not found: {config_path}")
except json.JSONDecodeError as e:
    print(f"❌ Error parsing config.json: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

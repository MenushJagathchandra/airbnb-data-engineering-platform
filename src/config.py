import os
import yaml
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
GOLD_DATA_DIR = DATA_DIR / "gold"

def load_config():
    config_path = CONFIG_DIR / "cities.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def ensure_directories():
    for directory in [RAW_DATA_DIR, CLEANED_DATA_DIR, GOLD_DATA_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    config = load_config()
    print("Configuration loaded successfully!")
    print(f"Cities configured: {[c['name'] for c in config['cities']]}")

import json
import os
from datetime import datetime

# Constants
CACHE_FILE = "/Users/markoristic/open-source/racunko/cache.json"

# Load cache from file or create new
def load_download_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save cache to file
def save_download_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Check if we need to reset or reuse cache
def should_reset_cache(cache):
    now = datetime.now()
    # add logic for dec -> Jan
    if now.month - 1 != 0:
      return cache.get("month") != (now.month - 1) or cache.get("year") != now.year
    else:
      return cache.get("month") != 12 or cache.get("year") != now.year - 1  
    

# Initialize or reset cache
def initialize_download_cache():
    cache = load_download_cache()
    if should_reset_cache(cache):
        now = datetime.now()
        print("🆕 New month detected, resetting cache.")
        return {"month": now.month - 1, "year": now.year}
    return cache

# Update cache after successful download
def mark_downloaded(cache, item_id):
    cache[item_id] = True
    save_download_cache(cache)

def mark_exists(cache, item_id):
    cache[item_id] = False
    save_download_cache(cache)

# Check if already downloaded
def is_downloaded(cache, item_id):
    return cache.get(item_id) is True

def is_all_true():
  data = load_download_cache()
  all_true = all(
    value is True for key, value in data.items()
    if isinstance(value, bool)
  )
  return all_true


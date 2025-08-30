import json
import os
import logging

logger = logging.getLogger("discord-bot.storage")

def ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")
        logger.info("Created data/ directory")
    # ensure files exist with defaults
    defaults = {
        "data/settings.json": {},
        "data/users.json": [],
        "data/reminders.json": [],
        "data/last_codes.json": []
    }
    for path, default in defaults.items():
        if not os.path.exists(path):
            try:
                with open(path, "w") as f:
                    json.dump(default, f, indent=2)
                logger.info(f"Created {path} with default content.")
            except Exception as e:
                logger.error(f"Failed creating {path}: {e}")

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        dirpath = os.path.dirname(path)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.exception(f"Failed to save {path}: {e}")


import json
import os

def get_config() -> dict:
    config = json.load(open("config.json"))
    if host := os.environ.get("POSTGRES_HOST"):
        config["postgres"]["host"] = host
    return config
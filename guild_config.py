import json
from pathlib import Path
from typing import Dict, Any, List

CONFIG_FILE = Path("data/guild_config.json")

# Type alias for guild configuration
ConfigDict = Dict[str, Any]

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def ensure_guild_config(config, guild_id):
    if str(guild_id) not in config:
        config[str(guild_id)] = {
            "logChannelId": None,
            "moderatorRoleId": None,
            "lastSeenBlacklistIds": [],
            "lastSeenUnblacklistIds": []
        }
    return config[str(guild_id)]

def set_log_channel(config, guild_id, channel_id):
    ensure_guild_config(config, guild_id)
    config[str(guild_id)]["logChannelId"] = channel_id
    save_config(config)

def set_mod_role(config, guild_id, role_id):
    ensure_guild_config(config, guild_id)
    config[str(guild_id)]["moderatorRoleId"] = role_id
    save_config(config)

def get_guild_config(config, guild_id):
    return ensure_guild_config(config, guild_id)



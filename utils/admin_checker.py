import json
import os
from typing import List

def load_admins(config_path: str = "./config/admins.json") -> List[str]:
    """
    Load the list of admin user IDs from the config file
    """
    if not os.path.exists(config_path):
        # Create a default config if it doesn't exist
        default_admins = {"admins": []}
        with open(config_path, 'w') as f:
            json.dump(default_admins, f, indent=2)
        return []
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config.get("admins", [])

def is_admin(user_id: str) -> bool:
    """
    Check if the given user ID is in the admin list
    """
    admins = load_admins()
    return str(user_id) in admins

def add_admin(admin_id: str) -> bool:
    """
    Add an admin to the config file
    """
    config_path = "./config/admins.json"
    admins = load_admins(config_path)
    
    if admin_id not in admins:
        admins.append(admin_id)
        with open(config_path, 'w') as f:
            json.dump({"admins": admins}, f, indent=2)
        return True
    return False

def remove_admin(admin_id: str) -> bool:
    """
    Remove an admin from the config file
    """
    config_path = "./config/admins.json"
    admins = load_admins(config_path)
    
    if admin_id in admins:
        admins.remove(admin_id)
        with open(config_path, 'w') as f:
            json.dump({"admins": admins}, f, indent=2)
        return True
    return False
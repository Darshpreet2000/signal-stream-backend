import os
from typing import Dict

def read_ccloud_config(config_file: str) -> Dict[str, str]:
    """
    Reads the client configuration from client.properties
    and returns it as a key-value map.
    
    Based on the ccloud-python-client sample.
    """
    config = {}
    if not os.path.exists(config_file):
        return config
        
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                try:
                    parameter, value = line.strip().split('=', 1)
                    config[parameter] = value.strip()
                except ValueError:
                    continue
    return config

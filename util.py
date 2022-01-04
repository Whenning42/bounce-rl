import json

def LoadJSON(filename):
    with open(filename) as f:
        loaded = json.load(f)
    return loaded

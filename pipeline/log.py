import json

def log_for_OAI_id(id, message):
    if isinstance(message, str):
        print(f"{id} : {message}")
    else:
        print(f"{id} : {json.dumps(message)}")

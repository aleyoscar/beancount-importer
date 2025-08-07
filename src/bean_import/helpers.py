import json, os

def cur(num): return '{:.2f}'.format(float(num))

def get_key(json_path, key):
    data = get_json(json_path)
    if key in data: return data[key]
    else: return None

def set_key(json_path, key, value):
    data = get_json(json_path)
    data[key] = value
    set_json(data, json_path)

def set_json(data, json_path):
    with open(json_path, 'w') as file:
        json.dump(data, file, indent=4, sort_keys=True, ensure_ascii=False)

def get_json(json_path):
    data = {}
    if not os.path.exists(json_path):
        set_json(data, json_path)
    with open(json_path, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            # If file is empty or invalid, initialize with empty dict
            set_json(data, json_path)
    return data

def get_json_values(json_path):
    return list(get_json(json_path).values())

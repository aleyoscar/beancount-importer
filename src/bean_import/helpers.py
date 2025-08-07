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

def replace_lines(console, file_path, new_data, line_start, line_count=1):
    new_data_arr = [l + '\n' for l in new_data.split('\n')]
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        new_lines = lines[:line_start - 1] + new_data_arr + lines[line_start + line_count - 1:]
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
    except Exception as e:
        console.print(f"[error]<<ERROR>> Error replacing lines: {str(e)}[/]")
        return False

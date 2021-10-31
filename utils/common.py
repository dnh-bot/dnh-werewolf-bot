import json

def read_json_file(filename):
    try:
        with open(filename, "r", encoding="utf8") as f:
            print(f"successfully loaded {filename}")
            return json.load(f)
    except Exception as e:
        print(e)
        return {}
import json
from collections import OrderedDict

def read_json_file(filename):
    try:
        with open(filename, "r", encoding="utf8") as f:
            print(f"successfully loaded {filename}")
            return json.load(f)
    except Exception as e:
        print("read json failed.", e)
        return {}

# Return 
#  True if the key is existing else return False
def update_json_file(filename, key, value):
    try:
        with open(filename, "r+", encoding="utf8") as f:
            print(f"successfully loaded {filename}")
            data = json.load(f)
            print(data)
            if data[key]:
                data[key] = value
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return True
            return False
    except Exception as e:
        print("update json failed.", e)
        return False
    




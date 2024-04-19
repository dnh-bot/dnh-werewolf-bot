import json


def read_json_file(filename):
    try:
        with open(filename, "r", encoding="utf8") as f:
            print(f"successfully loaded {filename}")
            return json.load(f)
    except Exception as e:
        print("read json failed.", e)
        return {}

def write_json_file(filename, data):
    try:
        with open(filename, "w", encoding="utf8") as f:
            print(f"successfully write {filename}")
            json.dump(data, f)
            # Add new line eof
            f.write('\n')
    except Exception as e:
        print("write json failed.", e)

def update_json_file(filename, key, value):
    """
    Check if the key exists.
    """
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
                # Add new line eof
                f.write('\n')
                return True
            return False
    except Exception as e:
        print("update json failed.", e)
        return False

def dict_to_list(cfg, number=0):
    yield from (name for name in cfg for _ in range(cfg[name]))
    yield from ('Werewolf' if i % 4 == 0 else 'Villager' for i in range(number - sum(cfg.values())))

import csv
import re
import json

pattern = "[A-z:0-9]+"

data = {}

def is_available_key(key):
    m = re.match(pattern, key)
    return m.group() if m is not None else None

def conv_key(key):
    key = key.replace("resources", "resource")
    return key

with open("./dataset.csv") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        value = row[3].strip()
        key = is_available_key(row[10].strip())
        if key is None:
            continue
        data[conv_key(key)] = value
        #.decode("utf-8")

print(data)

with open("./dataset.ts", "w") as f:
    dump = "export const DatasetTitles: { [key: string]: string } = "
    dump += json.dumps(data, indent=2).encode("raw_unicode_escape").decode("unicode_escape")
    f.write(dump)
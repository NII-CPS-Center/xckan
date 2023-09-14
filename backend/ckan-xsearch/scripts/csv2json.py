#!python3
# -*-coding:utf-8 -*-

import csv
import glob
import json

# select target csv
files = glob.glob("harvester/*.csv")
files.sort()
last = files[-1]

# generate list
sites = []
with open(last, 'r', encoding='utf_8_sig', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        name = row[1]
        url = row[2]
        list_api = row[3]
        show_api = list_api.replace('package_list', 'package_show')
        if list_api[0:4] != 'http':
            continue

        sites.append({
            "url": url,
            "name": name,
            "list_api": list_api,
            "show_api": show_api,
        })

# write as json
with open("ckanlist.json", 'w') as f:
    print(json.dumps(sites, indent=2, ensure_ascii=False), file=f)

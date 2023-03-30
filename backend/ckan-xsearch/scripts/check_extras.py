#!python3
# -*- coding: utf-8 -*-
import csv
import glob
import json

with open("extras.csv", "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Catalog', 'Dataset Name', 'Dataset Title', 'Extras'])

    for path in glob.glob('../catalog/*/*/.catalog.json'):
        dirs = path.split('/')
        with open(path, 'r') as f:
            metadata = json.load(f)

            if 'extras' in metadata['result']:
                extras = metadata['result']['extras']
                catalog = dirs[2]
                name = metadata['result']['name']
                title = metadata['result']['title']
                extras_json = json.dumps(extras, ensure_ascii=False)
                writer.writerow([catalog, name, title, extras_json])

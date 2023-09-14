#!python3
# -*-coding:utf-8 -*-

import glob
import os
import random
import shutil

files = glob.glob("catalog/*/*/*.csv")
nfiles = len(files)

shutil.rmtree('selection', ignore_errors=True)
os.makedirs('selection', 0o755)

for i in range(0, 500):
    r = random.randint(0, nfiles - 1)
    src = os.path.dirname(files[r])
    dst = "selection/" + src[8:]
    if os.path.exists(dst):
        i -= 1
        continue
    print("Copy tree from '{}' to '{}'".format(src, dst))
    shutil.copytree(src, dst)

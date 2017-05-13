#!/usr/bin/env python
# -*-python-*-
from __future__ import print_function;
import sys
import os
import re
import datetime

def move_one(src):
    src_base = os.path.basename(src)
    dst_base = src_base.replace(' ', '-').lower().replace('.jpeg', '.jpg')
    match = re.search('(20\d\d)[_-](\d\d)[_-](\d\d)', dst_base)
    if match:
        dst_dir = match.group(1) + '/' + match.group(2) + '-' + match.group(3)
    else:
        dt = datetime.datetime.fromtimestamp(os.path.getmtime(src))
        dst_dir = dt.strftime('%Y/%m-%d')
    dst_dir = os.path.join(os.environ['HOME'], 'Dropbox', 'Photos', dst_dir)
    if not os.path.isdir(dst_dir):
        parent = os.path.dirname(dst_dir)
        if not os.path.isdir(parent):
            os.mkdir(parent)
        os.mkdir(dst_dir)
    os.rename(src, os.path.join(dst_dir, dst_base))

if __name__ == '__main__':
    for f in sys.argv[1:]:
        move_one(f)

# -*- coding: utf-8 -*-
u"""Common code

:copyright: Copyright (c) 2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdlog
import datetime
import pykern.pkio
import re
import subprocess


IMAGE_SUFFIX = re.compile(
    r'\.(mp4|jpg|png|tif|gif|pcd|psd|mpg|pdf|mov|jpg|avi|thm|jpeg)$',
    flags=re.IGNORECASE,
)

MOVIE_SUFFIX = re.compile(
    r'\.(mp4|mov|mpg|avi)$',
    flags=re.IGNORECASE,
)


def move_one(src, dst_root):
    x = '%Y-%m-%d-%H.%M.%S'
    p = subprocess.run(
        ('exiftool', '-d', x, '-DateTimeOriginal', '-S', '-s', src),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    d = None
    if p.returncode != 0:
        pykern.pkcli.command_error('exiftool failed: {} {}'.format(src, p.stderr))
    t = p.stdout.strip()
    m = re.search(r'(20\d\d)[\D](\d\d)[\D](\d\d)', t)
    if m:
        d = m.group(1) + '/' + m.group(2) + '-' + m.group(3)
    else:
        pkdlog('using mtime: {}', src)
        d = datetime.datetime.fromtimestamp(src.mtime())
        t = d.strftime(x)
        d = d.strftime('%Y/%m-%d')
    if dst_root:
        d = dst_root.join(d)
        pykern.pkio.mkdir_parent(d)
    else:
        d = pykern.pkio.py_path('.')
    e = src.ext
    if e == '.jpeg':
        e = '.jpg'
    f = d.join(t + e)
    if f == src:
        pkdlog('ignoring same name: {}', src, f)
        return
    if f.exists():
        for i in range(1, 10):
            if f.read('rb') == src.read('rb'):
                pkdlog('ignoring duplicate contents: {} == {}', src, f)
                return
            f = d.join('{}-{}{}'.format(t, i, e))
            if not f.exists():
                break
        else:
            raise AssertionError('{}: exists'.format(f))
    if src.dirname == f.dirname:
        _fix_index(src.dirpath(), src.basename, f.basename)
        pkdlog('mv {} {}', src.basename, f.basename)
    src.rename(f)

    
def _fix_index(d, old, new):
    i = d.join('index.txt')
    if not i.exists():
        return
    r = []
    for l in i.read().split('\n'):
        if len(l.strip()) <= 0:
            continue
        if l.startswith(old):
            pkdlog('updating index: {} => {}', old, new)
            l = l.replace(old, new)
        r.append(l)
    i.write('\n'.join(r) + '\n')

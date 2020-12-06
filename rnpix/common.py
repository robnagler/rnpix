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

_MOVIES = 'mp4|mov|mpg|avi|mts'

_RAW = 'dng|arw'

_STILL = 'jpg|png|tif|gif|pcd|psd|pdf|thm|jpeg'

IMAGE_SUFFIX = re.compile(
    r'^(.+)\.({}|{}|{})$'.format(_STILL,_MOVIES, _RAW),
    flags=re.IGNORECASE,
)

MOVIE_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_MOVIES),
    flags=re.IGNORECASE,
)

RAW_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_RAW),
    flags=re.IGNORECASE,
)

STILL_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_STILL),
    flags=re.IGNORECASE,
)


def move_one(src, dst_root):
    e = src.ext.lower()
    if e == '.jpeg':
        e = '.jpg'
    x = '%Y-%m-%d-%H.%M.%S'
    # CreationDate is in timezone as is DateTimeOriginal
    y = '-CreationDate' if e == '.mov' else '-DateTimeOriginal'
    p = subprocess.run(
        ('exiftool', '-d', x, y, '-S', '-s', src),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    d = None
    if p.returncode != 0:
        pykern.pkcli.command_error('exiftool failed: {} {}'.format(src, p.stderr))
    t = p.stdout.strip()
    m = re.search(r'((?:20|19)\d\d)[\D](\d\d)[\D](\d\d)', t)
    if m:
        d = m.group(1) + '/' + m.group(2) + '-' + m.group(3)
    else:
        d = datetime.datetime.fromtimestamp(src.mtime())
        t = d.strftime(x)
        d = d.strftime('%Y/%m-%d')
        pkdlog('use mtime: {} => {}', src, t)
    if dst_root:
        d = dst_root.join(d)
        pykern.pkio.mkdir_parent(d)
    else:
        d = pykern.pkio.py_path('.')
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
    pkdlog('{}', f)
    return f


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

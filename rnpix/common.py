# -*- coding: utf-8 -*-
u"""Common code

:copyright: Copyright (c) 2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdlog, pkdp
import datetime
import pykern.pkio
import re
import subprocess

_MOVIES = 'mp4|mov|mpg|avi|mts|m4v'

_RAW = 'dng|arw'

_STILL = 'jpg|heic|png|tif|gif|pcd|psd|pdf|thm|jpeg'

IMAGE_SUFFIX = re.compile(
    r'^(.+)\.({}|{}|{})$'.format(_STILL, _MOVIES, _RAW),
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


THUMB_DIR = re.compile('^(?:200|50)$')


def move_one(src, dst_root):
    e = src.ext.lower()
    if e == '.jpeg':
        e = '.jpg'
    f1 = '%Y-%m-%d-%H.%M.%S'
    f2 = '{}-{}-{}-{}.{}.{}'
    # CreationDate is in timezone as is DateTimeOriginal but not for movies
    z = ('-CreationDate', '-CreationDateValue', '-createdate') if MOVIE_SUFFIX.search(src.basename) else ('-DateTimeOriginal',)
    d = None
    for y in z:
        p = subprocess.run(
            ('exiftool', '-d', f1, y, '-S', '-s', src),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if p.returncode != 0:
            pykern.pkcli.command_error('exiftool failed: {} {}'.format(src, p.stderr))
        m = re.search(r'((?:20|19)\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)', str(p.stdout))
        if m:
            # Creation Date Value is 2021:03:15 07:10:01-06:00
            # it's not a date, just a string but it has timezone
            t = f2.format(*m.groups())
            d = '{}/{}-{}'.format(*m.groups())
            break
    if not d:
        d = datetime.datetime.fromtimestamp(src.mtime())
        t = d.strftime(f1)
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
    pkdlog('src {}', src)
    if f.exists():
        for i in range(1, 10):
            if f.read('rb') == src.read('rb'):
                pkdlog('removing dup={} keep={}', src, f)
                src.remove(ignore_errors=True)
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
    pkdlog('dst {}', f)
    return f


def root():
    r = os.getenv('RNPIX_ROOT')
    assert r, 'must set $RNPIX_ROOT'
    return pykern.pkio.py_path(r)


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

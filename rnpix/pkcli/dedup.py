# -*- coding: utf-8 -*-
u"""deduplicate

:copyright: Copyright (c) 2021 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import dbm.ndbm
import hashlib
import os
import pykern.pkio
import re
import rnpix.common
import subprocess
import time


def find(path, nowrite=False, overwrite=False, skip=''):
    """deduplicate images using $RNPIX_ROOT/dedup.db
    """
    r = rnpix.common.root()
    i = 0
    if skip:
        skip = pykern.pkio.py_path(skip)
    with dbm.ndbm.open(
        str(pykern.pkio.py_path(r).join('dedup')),
        'c',
    ) as m:
        for p in _walk(path):
            if skip:
                if p == skip:
                    skip = None
                continue
            i += 1
            if i % 10 == 0:
                print('#sleep 3')
                time.sleep(2)
            s, p = _signature(p)
            if s in m and not overwrite:
                o = pykern.pkio.py_path(m[s].decode())
                if o == p:
                    # same path
                    continue
                if (
                    o.dirname == p.dirname
                    and o.purebasename.startswith(p.purebasename)
                ):
                    # remove original, because longer (e.g. x-1.jpg)
                    m[s] = str(p).encode()
                    p = o
                x = f'"{p}"' if "'" in str(p) else f"'{p}'"
                print(f'#OLD {m[s].decode()}\nrm {x}')
            else:
                print(f'#NEW {p}')
                if not nowrite:
                    m[s] = str(p).encode()


def not_in_db(path):
    """deduplicate images using $RNPIX_ROOT/dedup.db
    """
    r = rnpix.common.root()
    with dbm.ndbm.open(
        str(pykern.pkio.py_path(r).join('dedup')),
        'r',
    ) as m:
        v = set([m[k] for k in m.keys()])
    for p in _walk(path, print_cd=False):
        if str(p).encode() not in v:
            print(p)


def _signature(path):
    if path.ext.lower() in ('.jpg', '.jpeg'):
        try:
            return (subprocess.check_output(('identify', '-format', '%#', str(path))), path)
        except subprocess.CalledProcessError:
            # weird thing: bunch of JPG files that are quicktime movies
            if b'QuickTime movie' not in subprocess.check_output(('file', str(path))):
                raise
            n = path.new(ext='.mov')
            assert not n.exists()
            path.rename(n)
            path = n
    return (hashlib.md5(path.read_binary()).digest(), path)


def _walk(path, print_cd=True):
    c = ''
    for p in pykern.pkio.walk_tree(path):
        if (
            p.islink()
            or rnpix.common.THUMB_DIR.search(p.dirpath().basename)
            or not rnpix.common.STILL.search(p.basename)
        ):
            continue
        if print_cd and c != p.dirname:
            print(f'#CD {p.dirname}')
            c = p.dirname
        yield p

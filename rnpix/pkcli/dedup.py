# -*- coding: utf-8 -*-
u"""deduplicate

:copyright: Copyright (c) 2021 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import re
import time

def find(path, nowrite=False, overwrite=False):
    """deduplicate images using $RNPIX_ROOT/dedup.db
    """
    import pykern.pkio
    import dbm.ndbm
    import os
    import subprocess

    r = os.getenv('RNPIX_ROOT')
    assert r, 'must set $RNPIX_ROOT'
    i = 0
    with dbm.ndbm.open(
        str(pykern.pkio.py_path(r).join('dedup')),
        'c',
    ) as m:
        for p in _walk(path):
            i += 1
            if i % 10 == 0:
                print('#sleep 2')
                time.sleep(2)
            s = _signature(p)
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
            elif not nowrite:
                print(f'#NEW {p}')
                m[s] = str(p).encode()


def not_in_db(path):
    """deduplicate images using $RNPIX_ROOT/dedup.db
    """
    import pykern.pkio
    import dbm.ndbm
    import os

    r = os.getenv('RNPIX_ROOT')
    assert r, 'must set $RNPIX_ROOT'
    with dbm.ndbm.open(
        str(pykern.pkio.py_path(r).join('dedup')),
        'r',
    ) as m:
        v = set([m[k] for k in m.keys()])
    for p in _walk(path, print_cd=False):
        if str(p).encode() not in v:
            print(p)


def _signature(path):
    import hashlib
    import subprocess

    if path.ext.lower() in ('.jpg', '.jpeg'):
        return subprocess.check_output(('identify', '-format', '%#', str(path)))
    return hashlib.md5(path.read_binary()).digest()


def _walk(path, print_cd=True):
    import rnpix.common
    import pykern.pkio

    c = ''
    for p in pykern.pkio.walk_tree(path):
        if (
            p.islink()
            or rnpix.common.THUMB_DIR.search(p.dirpath().basename)
            or not rnpix.common.IMAGE_SUFFIX.search(p.basename)
        ):
            continue
        if print_cd and c != p.dirname:
            print(f'#CD {p.dirname}')
            c = p.dirname
        yield p

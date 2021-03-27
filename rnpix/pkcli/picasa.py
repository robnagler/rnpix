# -*- coding: utf-8 -*-
u"""deduplicate

:copyright: Copyright (c) 2021 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import re


def dedup(files):
    import pykern.pkio
    import os

    r = os.getenv('RNPIX_ROOT')
    assert r, 'must set $RNPIX_ROOT'
    r = pykern.pkio.py_path(r)
    z = r.join('picasa-remove')
    x = set(pykern.pkio.read_text(files).split('\n'))
    for f in sorted(x):
        p = pykern.pkio.py_path(f)
        if not f.check(file=True, exists=True):
            continue
        m = re.search(r'(.+)-\d+$', p.purebasename)
        if m:
            f = p.new(purebasename=m.group(1))
            # leave <date>.jpg even if it is picasa
            if not f.exists():
                continue
            f = None
        else:
            for i in range(1, 9):
                f = p.new(basename=p.basename.replace('.jpg', f'-{i}.jpg'))
                if f.exists() and str(f) not in x:
                    break
            else:
                continue
        t = z.join(p.relto(r))
        print(f'mkdir -p "{t.dirname}" && mv "{p}" "{t}"')
        if f:
            print(f'mv "{f}" "{p}"')

def find(path):
    """find images created by Google Picasa
    """
    import subprocess
    import pykern.pkio
    import os

    for p in _walk(path):
        if p.ext.lower() not in ('.jpg', '.jpeg'):
            continue
        if b'Picasa' in subprocess.check_output(
            ('exiftool', '-Creator', '-Artist', '-s', '-S', str(p))
        ):
            print(p)

def _walk(path):
    import rnpix.common
    import pykern.pkio
    import sys
    import time

    c = ''
    start = None # '2008-07-22'
    for p in pykern.pkio.walk_tree(path):
        if (
            p.islink()
            or rnpix.common.THUMB_DIR.search(p.dirpath().basename)
            or not rnpix.common.IMAGE_SUFFIX.search(p.basename)
        ):
            continue
        if start is not None:
            if p.dirpath().basename != start:
                continue
            start = None
        if c != p.dirname:
            c = p.dirname
            print(f'SLEEP: {c}', file=sys.stderr)
            time.sleep(3)
        yield p

# -*- coding: utf-8 -*-
u"""deduplicate

:copyright: Copyright (c) 2021 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import os
import pykern.pkio
import re
import rnpix.common
import subprocess
import sys
import time


def dedup(files, keep):
    r = os.getenv('RNPIX_ROOT')
    assert r, 'must set $RNPIX_ROOT'
    r = pykern.pkio.py_path(r)
    a = _split_file(files)
    k = _split_file(keep)
    print(
f'''#!/bin/bash
set -euo pipefail
export RNPIX_ROOT='{r}'
''' + '''
_mv() {
    local p=$1
    local f=${2:-}
    local t=$RNPIX_ROOT-trash${p#$RNPIX_ROOT}
    mkdir -p "$(dirname "$t")"
    mv "$p" "$t"
    if [[ $f ]]; then
        mv "$f" "$p"
    fi
}'''
    )
    for p in sorted(a):
        if not p.check(file=True, exists=True) or p in k:
            continue
        f = ''
        if not _remove_original(p, a):
            m = re.search(r'(.+)-\d+$', p.purebasename)
            if m:
                f = p.new(purebasename=m.group(1))
                # leave <date>.jpg even if it is picasa
                if not f.exists():
                    continue
                f = ''
            else:
                for i in range(1, 9):
                    f = p.new(basename=p.basename.replace('.jpg', f'-{i}.jpg'))
                    if f.exists() and str(f) not in a:
                        break
                else:
                    # no originals so should not get here
                    raise AssertionError(f'no originals {p}')
        print(f"_mv '{p}' '{f}'")


def find(path):
    """find images created by Google Picasa
    """
    for p in _walk(path):
        if p.ext.lower() not in ('.jpg', '.jpeg'):
            continue
        if b'Picasa' in subprocess.check_output(
            ('exiftool', '-Creator', '-Artist', '-s', '-S', str(p))
        ):
            print(p)


def _remove_original(path, all_picasa):
    b = path.purebasename
    m = re.search(r'(.+)-\d+$', b)
    if m:
        b = m.group(1)
    p = path.new(purebasename=b + '*')
    x = set(pykern.pkio.sorted_glob(p))
    # "keep" is this set so first print this set to see which
    # originals to keep and remove, then run again with keep
    return not x - all_picasa


def _split_file(path):
    return set([
        pykern.pkio.py_path(f) for f in re.split(
            r'\s*\n\s*',
            pykern.pkio.read_text(path),
        ) if f
    ])

def _walk(path):
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

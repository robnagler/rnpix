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
    r = rnpix.common.root()
    a = _split_file(files)
    k = _split_file(keep)
    print(
f'''#!/bin/bash
set -euo pipefail
export RNPIX_ROOT='{r}'
''' + '''
_mv() {
    local p=$1
    local o=${2:-}
    if [[ $o && ! -e $o || -e $p ]]; then
        return
    fi
    local t=$RNPIX_ROOT-trash${p#$RNPIX_ROOT}
    mkdir -p "$(dirname "$t")"
    mv "$p" "$t"
    if [[ $o ]]; then
        mv "$o" "$p"
    fi
}'''
    )
    for p in sorted(a):
        if not p.check(file=True, exists=True) or p in k:
            continue
        f = ''
        o = _originals(p, a)
        if not o:
            # no originals
            continue
        if not re.search(r'(.+)-\d+$', p.purebasename):
            for i in range(1, 9):
                f = p.new(basename=p.basename.replace('.jpg', f'-{i}.jpg'))
                if f in o:
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
        x = subprocess.check_output(
            ('exiftool', '-Creator', '-Artist', '-Orientation', str(p))
        )
        if b'Picasa' in x and 'Orientation' not in x:
            print(p)


def _originals(path, all_picasa):
    b = path.purebasename
    m = re.search(r'(.+)-\d+$', b)
    if m:
        b = m.group(1)
    p = path.new(purebasename=b + '*')
    return set(pykern.pkio.sorted_glob(p)) - all_picasa


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
            or not rnpix.common.STILL.search(p.basename)
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

# -*- coding: utf-8 -*-
u"""deduplicate

:copyright: Copyright (c) 2021 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import re


def default_command(path):
    """find images created by Google Picasa
    """
    import subprocess
    import pykern.pkio
    import os

    for p in _walk(path):
        if p.ext.lower() not in ('.jpg', '.jpeg'):
            continue
        if subprocess.check_output(
            ('exiftool', '-Creator', '-s', '-S', str(p))
        ) == b'Picasa\n':
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

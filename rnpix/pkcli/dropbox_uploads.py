#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""Rename Camera Uploads from Dropbox

:copyright: Copyright (c) 2014-2020 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp, pkdlog
import pykern.pkio
import rnpix.common
import contextlib
import errno
import os
import os.path
import time


def default_command(*dirs):
    """Move files to ~/Dropbox/Photos/YYYY/MM-DD

    Setup with Automator by Run Shell Script::

        exec > /Users/nagler/Desktop/rnpix-dropbox-uploads.log 2>&1
        source ~/.bashrc
        rnpix dropbox-uploads 'directory where files are uploaded'

    Make sure::

        Folder Action receives files and folders added to Camera Uploads

    If ``$RNPIX_ROOT`` set, will use that instead of ~/Dropbox/Photos

    Args:
        files (str): what to copy
    """
    r = pykern.pkio.py_path(
        os.getenv('RNPIX_ROOT', '~/Dropbox/Photos'),
    )
    t = set()
    for d in dirs:
        with _lock(d):
            d = pykern.pkio.py_path(d)
            for f in pykern.pkio.sorted_glob(d.join('/*.*')):
                if rnpix.common.IMAGE_SUFFIX.search(str(f)):
                    x = rnpix.common.move_one(f, r).dirname
                    if x:
                        t.add(x)
    return '\n'.join(sorted(t))


@contextlib.contextmanager
def _lock(filename):
    # Lock directories don't work within Dropbox folders, because
    # Dropbox uploads them and they can hang around after deleting here.
    lock_d = '/tmp/dropbox_uploads-' + os.environ['USER']
    lock_pid = os.path.join(lock_d, 'pid')

    def _pid():
        res = -1
        try:
            with open(lock_pid) as f:
                res = int(f.read())
        except Exception:
            pass
        pkdlog(res)
        if res <= 0:
            return res
        try:
            os.kill(res, 0)
        except Exception as e:
            pkdlog(e)
            if isinstance(e, OSError) and e.errno == errno.ESRCH:
                return res
        return -1

    is_locked = False
    try:
        for i in range(5):
            try:
                os.mkdir(lock_d)
                is_locked = True
                with open(lock_pid, 'w') as f:
                    f.write(str(os.getpid()))
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                pid = _pid()
                if pid <= 0:
                    time.sleep(.4)
                    continue
                if pid == _pid():
                    os.remove(lock_pid)
                    os.rmdir(lock_d)
        else:
            raise ValueError('{}: unable to create lock'.format(lock_d))
        yield lock_d
    finally:
        if is_locked:
            os.remove(lock_pid)
            os.rmdir(lock_d)

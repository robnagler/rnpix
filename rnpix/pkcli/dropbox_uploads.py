#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""Rename Camera Uploads from Dropbox

:copyright: Copyright (c) 2014-2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp
from rnpix import common
import contextlib
import datetime
import errno
import glob
import os
import os.path
import re
import sys
import time


def default_command(*files):
    """Move files to ~/Dropbox/Photos/YYYY/MM-DD

    Actually ignores the files, and instead searches
    the directory.

    Setup with Automator by Run Shell Script::

        . ~/.bashrc
        rnpix dropbox-uploads "$@"

    Make sure::

        Folder Action receives files and folders added to Camera Uploads

    Args:
        files (str): what to copy
    """
    dirs = set()
    for f in files:
        dirs.add(os.path.dirname(f))
    for d in dirs:
        with _lock(d):
            for f in glob.glob(os.path.join(d, '*.*')):
                if common.IMAGE_SUFFIX.search(f):
                    _move_one(f)


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
        pkdp(res)
        if res <= 0:
            return res
        try:
            os.kill(res, 0)
        except Exception as e:
            pkdp(e)
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


def _move_one(src):
    src_base = os.path.basename(src)
    dst_base = src_base.replace(' ', '-').lower().replace('.jpeg', '.jpg')
    match = re.search('(20\d\d)[_-](\d\d)[_-](\d\d)', dst_base)
    if match:
        dst_dir = match.group(1) + '/' + match.group(2) + '-' + match.group(3)
    else:
        dt = datetime.datetime.fromtimestamp(os.path.getmtime(src))
        dst_dir = dt.strftime('%Y/%m-%d')
    dst_dir = os.path.join(os.environ['HOME'], 'Dropbox', 'Photos', dst_dir)
    if not os.path.isdir(dst_dir):
        parent = os.path.dirname(dst_dir)
        if not os.path.isdir(parent):
            os.mkdir(parent)
        os.mkdir(dst_dir)
    os.rename(src, os.path.join(dst_dir, dst_base))

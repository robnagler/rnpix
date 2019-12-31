#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""Rename Camera Uploads from Dropbox

:copyright: Copyright (c) 2014-2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp, pkdlog
import pykern.pkio
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
import subprocess


def default_command():
    """Move files 

    Setup with Automator by Run Shell Script::

        . ~/.bashrc
        rnpix dropbox-uploads 'directory where files are uploaded'

    Make sure::

        Folder Action receives files and folders added to Camera Uploads

    Args:
        files (str): what to copy
    """
    for d in dirs:
        with _lock(d):
            for f in glob.glob(os.path.join(d, '*.*')):
                if common.IMAGE_SUFFIX.search(f):
                    _move_one(f)


def _fix_index(d, old, new):
    i = d.join('index.txt')
    if not i.exists():
        return
    r = []
    for l in i.read().split('\n'):
        if len(l.strip()) <= 0:
            continue
        if l.startswith(old):
            l = l.replace(old, new)
        r.append(l)
    i.write('\n'.join(r) + '\n')


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


def _move_one(src):
    x = '%Y-%m-%d-%H.%M.%S'
    t = subprocess.check_output(
        ('exiftool', '-d', x, '-DateTimeOriginal', '-S', '-s', src),
    ).decode().strip()
    s = pykern.pkio.py_path(src)
    e = s.ext
    if e == '.jpeg':
        e = '.jpg'
    m = re.search(r'(20\d\d)[\D](\d\d)[\D](\d\d)', t)
    if m:
        d = m.group(1) + '/' + m.group(2) + '-' + m.group(3)
    else:
        d = datetime.datetime.fromtimestamp(s.mtime())
        d = d.strftime('%Y/%m-%d')
        t = d.strftime(x)
    d = pykern.pkio.py_path('~').join('Dropbox', 'Photos', d)
    pykern.pkio.mkdir_parent(d)
    f = d.join(t + e)
    if f == s:
        print('{} already in proper form'.format(s))
        return
    if f.check():
        for i in range(1, 10):
            f = d.join('{}-{}{}'.format(t, i, e))
            if not f.check():
                break
        else:
            raise AssertionError('{}: exists'.format(f))
    if s.dirname == f.dirname:
        _fix_index(s.dirpath(), s.basename, f.basename)
    s.rename(f)


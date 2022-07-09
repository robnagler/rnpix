# -*- coding: utf-8 -*-
u"""Common code

:copyright: Copyright (c) 2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdlog, pkdp
import contextlib
import datetime
import errno
import os
import os.path
import pykern.pkio
import re
import subprocess
import time


_MOVIES = 'mp4|mov|mpg|avi|mts|m4v'

_STILL_TO_JPG = 'dng|pcd|arw'

_STILL = 'jpg|heic|png|tif|gif|psd|pdf|thm|jpeg'

IMAGE_SUFFIX = re.compile(
    r'^(.+)\.({}|{}|{})$'.format(_STILL, _MOVIES, _STILL_TO_JPG),
    flags=re.IGNORECASE,
)

MOVIE_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_MOVIES),
    flags=re.IGNORECASE,
)

STILL_TO_JPG_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_STILL_TO_JPG),
    flags=re.IGNORECASE,
)

STILL_SUFFIX = re.compile(
    r'^(.+)\.({})$'.format(_STILL),
    flags=re.IGNORECASE,
)


THUMB_DIR = re.compile('^(?:200|50)$')


@contextlib.contextmanager
def user_lock():
    # Lock directories don't work within Dropbox folders, because
    # Dropbox uploads them and they can hang around after deleting here.
    lock_d = '/tmp/rnpix-lock-' + os.environ['USER']
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

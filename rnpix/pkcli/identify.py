# -*- coding: utf-8 -*-
u"""Identify photos and store in index.txt database.

The directory structure of pictures is <rnpix_root>/yyyy/mm-dd/*.{jpg,png,...}
Each day directory has index.txt, which is edited by this program.

https://github.com/cebe/js-search

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rnpix import common
import glob
import os
import os.path
import re
import six
import subprocess
import sys
import uuid


def add_to_index(*date_dir):
    """Search in date_dir or all dirs in year
    """
    if date_dir:
        for d in date_dir:
            _one_day(date_dir)
    elif _search_all_dirs(True) is None:
        _one_day(_need_to_index())


def need_to_index():
    """Where to index
    """
    res = _search_all_dirs(False)
    assert not res is None, \
        'must be executed from <rnpix_root>/<year> directory'
    return res


def _clean_name(old):
    new = re.sub(r'[^\-\.\w]+', '-', old.lower())
    new = re.sub(r'\.(jpeg|thm)$', '.jpg', new)
    if new == old:
        return old
    if new == old.lower():
        tmp = str(uuid.uuid4())
        assert not os.path.exists(tmp), \
            '{}: tmp file exists, cannot rename {}'.format(tmp, old)
        os.rename(old, tmp)
    else:
        tmp = old
    assert not os.path.exists(new), \
        '{}: new file exists, cannot rename {}'.format(new, tmp)
    os.rename(tmp, new)
    return new


def _indexed():
    res = {}
    if not os.path.exists('index.txt'):
        return res
    with open('index.txt', 'r') as f:
        p = re.compile(r'^[^\s:]+')
        for l in f:
            l = l.rstrip()
            if not l:
                continue
            if l.startswith('#'):
                continue
            m = p.search(l)
            if not m:
                print(l + ': invalid line')
                continue
            t = m.group(0)
            if not os.path.exists(t):
                print(t + ': indexed file does not exist')
                continue
            res[t] = 1
    return res


def _need_to_index():
    indexed = _indexed()
    res = set()
    t = set()
    for a in sorted(os.listdir('.'), key=str.lower):
        if not common.IMAGE_SUFFIX.search(a):
            continue
        a = _clean_name(a)
        m = common.RAW_SUFFIX.search(a)
        if m and os.path.exists(m.group(1) + '.jpg'):
            # pcd or arw with a jpg preview already there
            continue
        m = common.MOVIE_SUFFIX.search(a)
        if m:
            x = m.group(1) + '.jpg'
            if os.path.exists(x):
                # don't index thumbs
                t.add(x)
        if a in indexed:
            continue
        res.add(a)
    return sorted(res - t)


def _one_day(args):
    """Prompts for index file update

    `_need_to_index` has already filtered jpg preferred over other
    formats, that is, if there is a duplicate name, it will list the
    jpg, not the arw, pcd, etc. in the index.

    Args:
        args (list): files to index

    """
    def _extract_jpg(image):
        for e, s in (
            # You can view arw files by modifying the camera type:
            # exiftool -sonymodelid="ILCE-7M2" -ext ARW
            # but better to extract the jpg preview and not modify the
            # camera type
            ('arw', ['exiftool', '-b', '-PreviewImage', image]),
            # Suffix [5] produces an image 3072 by 2048 ("16 Base")
            ('pcd', ['convert', image + '[5]']),
        ):
            if not image.endswith('.' + e):
                continue
            p = re.sub(f'\\.{e}$', '.jpg', image)
            if e == 'pcd':
                s.append(p)
            i = subprocess.check_output(s)
            with open(p, 'wb') as f:
                f.write(i)
            return p
        return image

    if not args:
        return
    cwd = os.getcwd()
    simple_msg = None
    for a in args:
        img = os.path.basename(a)
        d = os.path.dirname(a)
        if d:
            os.chdir(d)
        if not os.path.exists(img):
            continue
        preview = _extract_jpg(img)
        if simple_msg:
            msg = simple_msg
        else:
            if common.MOVIE_SUFFIX.search(img):
                subprocess.check_call(['open', '-a', 'QuickTime Player.app', img])
            else:
                subprocess.check_call(['open', '-a', 'Preview.app', preview])
            msg = input(a + ': ')
            if not msg:
                status = False
                break
            if msg == '?':
                simple_msg = msg
        if os.path.exists(img):
            if msg == '!':
                os.remove(img)
                if preview != img:
                    os.remove(preview)
                print(a + ': removed')
            else:
                with open('index.txt', 'a') as f:
                    f.write(preview + ' ' + msg + '\n')
        else:
            print(a + ': does not exist')
        if d:
            os.chdir(cwd)
    try:
        os.remove('index.txt~')
    except Exception:
        pass
    return


def _search_all_dirs(addToIndex):
    cwd = os.getcwd()
    dirs = glob.glob('[0-9][0-9]-[0-9][0-9]')
    if not dirs:
        return None
    res = []
    for d in dirs:
        try:
            os.chdir(d)
            files = _need_to_index()
            if files:
                res.append(d)
                if addToIndex:
                    _one_day(files)
        finally:
            os.chdir(cwd)
    return sorted(res)

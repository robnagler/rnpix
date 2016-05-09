# -*- coding: utf-8 -*-
u"""?

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

from pykern import pkio
from pykern.pkdebug import pkdp
import glob
import os
import os.path
import shutil
import py.path
import re

_LINE_RE = re.compile(r'^([^\s:]+):?\s*(.*)')

_IMAGE_RE = re.compile(r'^(.+)\.(mp4|jpg|gif|tif|pcd|png|pdf|mov|jpg|thm|jpeg)$', flags=re.IGNORECASE)

def default_command():
    """Find all dirs and try to fix"""
    for f in pkio.walk_tree('.', file_re=r'index.txt$'):
        with pkio.save_chdir(f.dirname):
            _one_dir()
    

def _one_dir():
    d = os.getcwd()
    pkdp('{}', d)
    def err(msg):
        pkdp('{}: {}'.format(d, msg))
    try:
        with open('index.txt') as f:
            lines = list(f)
    except:
        return
    images = set()
    bases = {}
    for x in glob.glob('*.*'):
        m = _IMAGE_RE.search(x)
        if m:
            images.add(x)
            # There may be multiple but we are just using for anything
            # to match image bases only
            bases[m.group(1)] = x
    new_lines = []
    for l in lines:
        if l.startswith('#'):
            new_lines.append(l)
            continue
        m = _LINE_RE.search(l)
        if not m:
            if re.search(r'\S', l):
                err('{}: strange line, commenting'.format(l))
                new_lines.append('#' + l)
            err('{}: blank line, skipping'.format(l))
            continue
        i, t = m.group(1, 2)
        m = _IMAGE_RE.search(i)
        if not m:
            if i in bases:
                err('{}: substituting for {}'.format(i, bases[i]))
                i = bases[i]
                l = i + ' ' + t + '\n'
            else:
                err('{}: no such base or image, commenting'.format(i))
                new_lines.append('#' + l)
                continue
        if i in images:
            images.remove(i)
        else:
            err('{}: no such image: text={}'.format(i, t))
            new_lines.append('#' + l)
            continue
        if not len(t):
            err('{}: no text, adding "?"'.format(l))
            l = i + ' ?\n'
        new_lines.append(l)
            
    if images:
        err('{}: extra images, append'.format(images))
        for i in images:
            new_lines.append(i + ' ?\n')
    if new_lines != lines:
        pkdp('writing: index.txt')
        os.rename('index.txt', 'index.txt~')
        with open('index.txt', 'w') as f:
            f.write(''.join(new_lines))
        shutil.copymode('index.txt~', 'index.txt')

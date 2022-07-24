# -*- coding: utf-8 -*-
"""?

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp
import glob
import os
import os.path
import py.path
import pykern.pkcli
import pykern.pkio
import re
import rnpix.common
import shutil


_LINE_RE = re.compile(r"^([^\s:]+):?\s*(.*)")


def files(*files, dst_root=None):
    if not files:
        pykern.pkcli.command_error("must supply files")
    for f in files:
        rnpix.common.move_one(
            pykern.pkio.py_path(f),
            dst_root and pykern.pkio.py_path(dst_root),
        )


def v1():
    """Find all dirs and try to fix"""
    for f in pykern.pkio.walk_tree(".", file_re=r"index.txt$"):
        with pykern.pkio.save_chdir(f.dirname):
            _one_dir()


def _one_dir():
    d = os.getcwd()
    pkdp("{}", d)

    def err(msg):
        pkdp("{}: {}".format(d, msg))

    try:
        with open("index.txt") as f:
            lines = list(f)
    except:
        return
    images = set()
    bases = {}
    seen = set()
    for x in glob.glob("*.*"):
        m = rnpix.common.STILL.search(x)
        if m:
            images.add(x)
            # There may be multiple but we are just using for anything
            # to match image bases only
            bases[m.group(1)] = x
    new_lines = []
    for l in lines:
        if re.search(r"^#\S+\.avi", l):
            # Fix previous avi bug
            l = l[1:]
        elif re.search(r"^#\d+_\d+\.jpg", l):
            l = l[1:].replace("_", "-", 1)
        elif l.startswith("#"):
            new_lines.append(l)
            continue
        m = _LINE_RE.search(l)
        if not m:
            if re.search(r"\S", l):
                err("{}: strange line, commenting".format(l))
                new_lines.append("#" + l)
            err("{}: blank line, skipping".format(l))
            continue
        i, t = m.group(1, 2)
        m = rnpix.common.STILL.search(i)
        if not m:
            if i in bases:
                err("{}: substituting for {}".format(i, bases[i]))
                i = bases[i]
                l = i + " " + t + "\n"
            else:
                err("{}: no such base or image, commenting".format(i))
                new_lines.append("#" + l)
                continue
        if i in images:
            images.remove(i)
            seen.add(i)
        else:
            if i in seen:
                if t == "?":
                    err("{}: already seen no text, skipping".format(i))
                    continue
                err("{}: already seen with text".format(i))
            err("{}: no such image: text={}".format(i, t))
            new_lines.append("#" + l)
            continue
        if not len(t):
            err('{}: no text, adding "?"'.format(l))
            l = i + " ?\n"
        new_lines.append(l)

    if images:
        err("{}: extra images, append".format(images))
        for i in images:
            new_lines.append(i + " ?\n")
    if new_lines != lines:
        pkdp("writing: index.txt")
        os.rename("index.txt", "index.txt~")
        with open("index.txt", "w") as f:
            f.write("".join(new_lines))
        shutil.copymode("index.txt~", "index.txt")

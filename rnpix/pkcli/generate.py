# -*- coding: utf-8 -*-
"""?

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

from pykern import pkcli
from pykern import pkio
from pykern.pkdebug import pkdp, pkdlog
import glob
import html
import os
import os.path
import py.path
import re
import subprocess

# for f in *.jpg; do convert -resize x200 -quality 50% $f t\
#    /$f; done
# https://github.com/cebe/js-search

_DIR_RE = re.compile(r"/(\d{4})/(\d\d)-(\d\d)$")

_MM_DD = "[0-9][0-9]-[0-9][0-9]"
_YYYY_MM_DD = "[0-9][0-9][0-9][0-9]/" + _MM_DD

_HTML = """<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" type="text/css" href="../../rnpix/package_data/static/rnpix.css">
<title>{title}</title>
</head>
<body class="rnpix_day">
<span class="rnpix_head"><span class="rnpix_title">{title}</span><a class="rnpix_button" href="../../index.html">Search</a></span>
{body}
</body>
</html>
"""

_IMG_HTML = (
    "<figure><img src='{thumb}' onclick='this.src="
    + '"{image}"'
    + "' /><figcaption>{caption}</figcaption></figure>\n"
)

_LINE_RE = re.compile(r"^(.+?):?\s+(.+)")

_INDEX_FILE = "index.html"


def default_command(force=False):
    """Generate index.html files in mm-dd subdirectories

    Args:
        force (bool): force thumbs and indexes even if they exist
    """
    if _DIR_RE.search(os.getcwd()):
        _one_dir(force)
    else:
        dirs = list(glob.iglob(_MM_DD))
        if not dirs:
            dirs = list(glob.iglob(_YYYY_MM_DD))
            if not dirs:
                pkcli.command_error("no directories matching YYYY or MM-DD")
        for d in sorted(dirs):
            with pkio.save_chdir(d):
                _one_dir(force)


def _index_parser(lines, err, force):
    body = ""
    for l in lines:
        if l.startswith("#"):
            continue
        m = _LINE_RE.search(l)
        if not m:
            if re.search(r"\S", l):
                err("invalid line: " + l)
            continue
        i = m.group(1)
        body += _IMG_HTML.format(
            image=i,
            thumb=_thumb(i, force),
            caption=html.escape(m.group(2)),
        )
    return body


def _one_dir(force):
    d = os.getcwd()

    def err(msg):
        pkdp("{}: {}".format(d, msg))

    m = _DIR_RE.search(d)
    if not m:
        err("directory does not match date format")
        return
    title = "{:d}/{:d}/{:d}".format(int(m.group(2)), int(m.group(3)), int(m.group(1)))
    try:
        with open("index.txt") as f:
            lines = list(f)
    except IOError:
        err("no index.txt")
        return
    body = _index_parser(lines, err, force)
    with open(_INDEX_FILE, "w") as f:
        f.write(_HTML.format(title=title, body=body))


def _thumb(image, force):
    """Returns larger size"""
    width = "200"
    quality = "50"
    t = re.sub(r"\w+$", "jpg", image)
    if os.path.exists(t):
        image = t
    t = os.path.join(width, t)
    if force or not os.path.exists(t):
        d = pkio.mkdir_parent(py.path.local(t).dirname)
        try:
            subprocess.check_call(
                [
                    "convert",
                    "-thumbnail",
                    "x" + width,
                    "-quality",
                    quality + "%",
                    "-background",
                    "white",
                    "-alpha",
                    "remove",
                    image + "[0]",
                    t,
                ]
            )
        except Exception:
            pkdlog("dir={}", d)
            raise
    return t

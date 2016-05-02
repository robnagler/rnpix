# -*- coding: utf-8 -*-
u"""?

:copyright: Copyright (c) 2016 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

from pykern.pkdebug import pkdp
from pykern import pkio
import cgi
import glob
import os
import os.path
import re
import subprocess

# for f in *.jpg; do convert -resize x200 -quality 50% $f t\
#    /$f; done
# https://github.com/cebe/js-search

_DIR_RE = re.compile(r'/(\d{4})/(\d\d)-(\d\d)$')

_HTML = """<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" type="text/css" href="../../rnpix/package_data/static/pix.css">
<title>{title}</title>
</head>
<body class="rnpix">
{body}
</body>
</html>
"""

_IMG_HTML = "<figure><img src='{thumb}' onclick='this.src=" + '"{image}"' + "' /><figcaption>{caption}</figcaption></figure></a>\n"

_LINE_RE = re.compile(r'^(.+?):?\s+(.+)')

_INDEX_FILE = 'index.html'

_THUMB_DIR = 't'

def default_command(redo=False):
    """Generate index.html files in mm-dd subdirectories

    Args:
        redo (bool): redo thumbs and indexes even if they exist
    """
    if _DIR_RE.search(os.getcwd()):
        _one_dir(redo)
    else:
        for d in sorted(list(glob.glob('[0-9][0-9]-[0-9][0-9]'))):
            with pkio.save_chdir(d):
                _one_dir(redo)


def _index_parser(lines, err, redo):
    body = ''
    for l in lines:
        m = _LINE_RE.search(l)
        if not m:
            err('invalid line: ' + l)
            continue
        i = m.group(1)
        body += _IMG_HTML.format(
            image=i,
            thumb=_thumb(i, redo),
            caption=cgi.escape(m.group(2)),
        )
    return body


def _one_dir(redo):
    d = os.getcwd()
    def err(msg):
        pkdp('{}: {}'.format(d, msg))
    if not os.path.exists('index.txt'):
        err('no index.txt')
        return
    m = _DIR_RE.search(d)
    if not m:
        err('directory does not match date format')
        return
    title = '{:d}/{:d}/{:d}'.format(
        int(m.group(2)), int(m.group(3)), int(m.group(1)))
    with open('index.txt') as f:
        body = _index_parser(list(f), err, redo)
    if redo or not os.path.exists(_INDEX_FILE):
        with open(_INDEX_FILE, 'w') as f:
            f.write(_HTML.format(title=title, body=body))


def _thumb(image, redo):
    t = re.sub(r'\w+$', 'jpg', os.path.join(_THUMB_DIR, image))
    if redo or not os.path.exists(t):
        pkio.mkdir_parent(_THUMB_DIR)
        subprocess.check_call(['convert', '-thumbnail', 'x200', '-background', 'white', '-alpha', 'remove', image + '[0]', t])
    return t

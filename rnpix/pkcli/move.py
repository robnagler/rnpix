"""Rename Camera Uploads from Dropbox

:copyright: Copyright (c) 2014-2020 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import pykern.pkio
import rnpix.common


def default_command(*dirs):
    """Move files to ~/Dropbox/Photos/YYYY/MM-DD

    Setup with Automator by Run Shell Script::

        exec > /Users/nagler/Desktop/rnpix-dropbox-uploads.log 2>&1
        source ~/.bashrc
        RNPIX_ROOT=~/Dropbox/Photos rnpix dropbox-uploads ~/Dropbox/Camera\ Uploads

    Make sure::

        Folder Action receives files and folders added to Camera Uploads

    And check::

        Finder > Camera Uploads > Right-Click > Services > Folder Actions Setup

    ``$RNPIX_ROOT`` must be set.

    Args:
        dirs (str): driectories to copy (not recursive)
    """
    r = rnpix.common.root()
    t = set()
    for d in dirs:
        with rnpix.common.user_lock():
            d = pykern.pkio.py_path(d)
            for f in pykern.pkio.sorted_glob(d.join("/*.*")):
                if rnpix.common.KNOWN_EXT.search(str(f)):
                    x = rnpix.common.move_one(f, r)
                    if x:
                        t.add(x.dirname)
    return "\n".join(sorted(t))

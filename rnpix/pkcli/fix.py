"""utilities to fix photos

:copyright: Copyright (c) 2016-2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp, pkdlog
import datetime
import exif
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

_WEEK = datetime.timedelta(days=7)


def exif_data(*paths, dry_run=False):
    index_cache = PKDict()

    def _check(path):
        nonlocal index_cache

        path = pykern.pkio.py_path(path)
        if path.ext != ".jpg":
            return False
        return _check_glob(path) and _ExifData(path, index_cache).need_update()

    def _check_glob(path):
        l = pykern.pkio.sorted_glob(str(path.new(ext=".*")))
        if len(l) == 0:
            raise AssertionError(f"no matches path={path}")
        if list(filter(lambda x: x.ext in (".pcd", ".png"), l)):
            raise ValueError(f"pcd or png in glob={l}")
        return len(l) == 1

    def _update(path):
        if d := _check(path):
            if dry_run:
                return d.path
            return d.update()
        return None

    if not paths:
        pykern.pkcli.command_error("must supply paths")
    return tuple(sorted(filter(bool, map(_update, paths))))


def relocate(*files, dst_root=None):
    if not files:
        pykern.pkcli.command_error("must supply files")
    for f in files:
        rnpix.common.move_one(
            pykern.pkio.py_path(f),
            dst_root and pykern.pkio.py_path(dst_root),
        )


class _ExifData:
    def __init__(self, path, index_cache):
        def _desc(index_path):
            if (i := index_cache.get(index_path)) is None:
                i = index_cache[index_path] = rnpix.common.index_parse(index_path)
            return i.get(self.path.basename)

        self.path = path
        with self.path.open("rb") as f:
            self.img = exif.Image(f)
        self.path_dt = rnpix.common.date_time_parse(self.path)
        if not self.path_dt:
            raise ValueError(f"no date time in path={path}")
        # Always returns something valid
        self.exif = rnpix.common.exif_parse(self.img)
        self.desc = _desc(self.path.dirpath())

    def need_update(self):
        if "-01.01.01" in self.path.purebasename:
            raise ValueError(f"need to rename with _NN path={path}")
        self.need_dt = (
            not self.exif.date_time or abs(self.path_dt - self.exif.date_time) > _WEEK
        )
        self.need_desc = bool(self.desc) and self.exif.description != self.desc
        return self if self.need_dt and self.need_desc else None

    def update(self):
        k = PKDict(path=self.path)
        if self.need_desc:
            k.description = self.desc
        if self.need_dt:
            k.date_time = self.path_dt
        rnpix.common.exif_set(self.img, **k)
        return self.path

    def _path_dt(self):
        if (rv := rnpix.common.date_time_parse(self.path)) is None:
            raise ValueError(f"no match path={path}")
        return rv

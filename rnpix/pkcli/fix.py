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

_DATE_TIME = re.compile(
    r"^((?:18|19|20)\d\d)\D?(\d\d)\D?(\d\d)\D?(\d\d)\D?(\d\d)\D?(\d\d)"
)
_DATE_N = re.compile(r"((?:18|19|20)\d\d)\D?(\d\d)\D?(\d\d)\D+(\d*)")

_WEEK = datetime.timedelta(days=7)


def date_time(*paths):
    def _check(path):
        if path.ext != ".jpg":
            return False
        return _DateTimeFix(path).need_update()

    if not paths:
        pykern.pkcli.command_error("must supply paths")
    return [p for p in paths if _check(pykern.pkio.py_path(p))]


def relocate(*files, dst_root=None):
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


class _DateTimeFix:
    def __init__(self, path):
        self.path = path
        with self.path.open("rb") as f:
            self.img = exif.Image(f)
        self.path_dt = self._path_dt()
        self.exif_dt = self._exif_dt()

    def need_update(self):
        if "-01.01.01" in self.path.purebasename:
            raise ValueError(f"need to rename with _NN path={path}")
        return not self.exif_dt or abs(self.path_dt - self.exif_dt) > _WEEK

    def update(self):
        self.img.datetime_original = self.path_dt
        with self.path.open("wb") as f:
            f.write(self.img.get_file())

    def _exif_dt(self):
        if not (d := getattr(self.img, "datetime_original", None)):
            return None
        if z := getattr(self.img, "offset_time_original", None):
            return datetime.datetime.strptime(d + z, "%Y:%m:%d %H:%M:%S%z").astimezone(
                datetime.timezone.utc
            )
        return datetime.datetime.strptime(d, "%Y:%m:%d %H:%M:%S")

    def _path_dt(self):
        if m := _DATE_TIME.search(self.path.purebasename):
            d = m.groups()
        elif (m := _DATE_N.search(self.path.purebasename)) or (
            m := _DATE_N.search(str(self.path))
        ):
            d = [m.group(1), m.group(2), m.group(3), 12]
            s = int(m.group(4) or 0)
            d.extend((s // 60, s % 60))
        else:
            raise ValueError(f"no match path={path}")
        return datetime.datetime(*list(map(int, d)))


def _one_dir():
    d = os.getcwd()
    pkdlog("{}", d)

    def err(msg):
        pkdlog("{}: {}".format(d, msg))

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
        pkdlog("writing: index.txt")
        os.rename("index.txt", "index.txt~")
        with open("index.txt", "w") as f:
            f.write("".join(new_lines))
        shutil.copymode("index.txt~", "index.txt")

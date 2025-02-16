"""utilities to fix photos

:copyright: Copyright (c) 2016-2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.collections import PKDict
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

# Need to fix: 1934/12-29/1934-12-29-01.01.01.jpg
#                                             yyyy        mm        dd       HH       MM       SS
_DATE_TIME_RE = re.compile(r"(?:^|/)((?:18|19|20)\d\d)\D?(\d\d)\D?(\d\d)\D?(?:(\d\d)\D?(\d\d)\D?(\d\d))?")

def datetime_original(*paths):
    seen = PKDict()
    def _datetime_original(img):
        if not (d := getattr(img, 'datetime_original')):
            return None
        if z := getattr(img, 'offset_time_original'):
            return datetime.datetime.strptime(d + z, "%Y:%m:%d %H:%M:%S%z").astimezone(datetime.timezone.utc)
        return datetime.datetime.strptime(d, "%Y:%m:%d %H:%M:%S")

    def _datetime_file(path):
# deal with mp4 that has a jpg thumbnail (remove the thumbnail)
# create symlinks for all files that we will be copying
# ignoring 200 directories

# gif seems to map to avi, which need to be converted
????-??-??-??.??.??-?.gif
????-??-??-??.??.??.gif

# movies
skip, these are thumbnails so if there is a mov or mp4
ch??.jpg
dylan-????-and-????.jpg
dylan-birth.jpg
dylan-tea.jpg
janis_emma_????.jpg


# skip these, they are in ./2021/10-18 and emma pictures
????????_???-edit-?.jpg
????????_???-edit.jpg
# also 10-18 and have datetimes already set
????????_???.jpg

# convert png to jpg and then set datetime
????-??-??-??.??.??.png


# All these would be in order so just add number of seconds
??.jpg
????-??-??-?.jpg
# why would this exis
????-??-??-??.??.??-?.jpg
????-??-??-??.??.??-??.jpg
????-??-??-??.??.??.jpg
????-??-??-??.jpg
# Only problem is this so ok to have the same timestamp actually
????-??-??.??.??.??-?.jpg
????-??-??.??.??.??.jpg
????-??-??.jpg
????-??-??_?.jpg
????-??-??_??.jpg
????-??-??_????.jpg


        # deal with 01.01.01
        # otherwise
        parse the info.datetime_original to see if it close to the date
        on the file, that is, the date part is the same. if it is,
        do not update. otherwise, return path info
        need to _move_one() if the name is a mismatch and then update index

    def _update(path):
        with path.open("rb") as f:
            i = exif.Image(f)
        i.datetime_original = _date(path, i)
        with path.open("wb") as f:
            f.write(i.get_file())

    if not files:
        pykern.pkcli.command_error("must supply files")
    for f in files:
        _update(pykern.pkio.py_path(f))

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

"""Common code

:copyright: Copyright (c) 2017-2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import contextlib
import datetime
import errno
import exif
import os
import os.path
import pykern.pkio
import re
import subprocess
import time


_MOVIES = "3gp|mp4|mov|mpg|avi|mts|m4v"

# icns is for unit testing
_NEED_JPG = "icns|dng|pcd|arw|skp"

_STILL = "jpg|heic|png|tif|gif|psd|pdf|thm|jpeg"

KNOWN_EXT = re.compile(
    r"^(.+)\.({}|{}|{})$".format(_STILL, _MOVIES, _NEED_JPG),
    flags=re.IGNORECASE,
)

MOVIE = re.compile(
    r"^(.+)\.({})$".format(_MOVIES),
    flags=re.IGNORECASE,
)

NEED_PREVIEW = re.compile(
    r"^(.+)\.({})$".format(_NEED_JPG + "|" + _MOVIES),
    flags=re.IGNORECASE,
)

THUMB_DIR = re.compile("^(?:200|50)$")

INDEX_LINE = re.compile(r"^([^\s:]+)\s*(.*)")

MISSING_DESC = "?"

# Creation Date Value is 2021:03:15 07:10:01-06:00
# it's not a date, just a string but it has timezone
DATE_TIME_RE = re.compile(r"((?:18|19|20)\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)\D(\d\d)")

# Also includes a trailing diit possibly
DATE_RE = re.compile(r"((?:18|19|20)\d\d)\D?(\d\d)\D?(\d\d)\D+(\d*)")

BASE_FTIME = "%Y-%m-%d-%H.%M.%S"
BASE_FMT = "{}-{}-{}-{}.{}.{}"
DIR_FMT = "{}/{}-{}"
DIR_FTIME = "%Y/%m-%d"

ORIGINAL_FTIME = "%Y:%m:%d %H:%M:%S"


def date_time_parse(path):
    if m := DATE_TIME_RE.search(path.purebasename):
        d = m.groups()
    elif (m := DATE_RE.search(path.purebasename)) or (m := DATE_RE.search(str(path))):
        d = [m.group(1), m.group(2), m.group(3), 12]
        s = int(m.group(4) or 0)
        d.extend((s // 60, s % 60))
    else:
        return None
    return datetime.datetime(*list(map(int, d)))


def exif_image(readable):
    if isinstance(readable, exif.Image):
        return readable
    # Handle py.path
    if a := getattr(readable, "open", None):
        readable = a("rb")
    return exif.Image(readable)


def exif_parse(readable):
    def _date_time(exif_image, date_time):
        if date_time is None:
            return None
        if z := getattr(exif_image, "offset_time_original", None):
            return (
                datetime.datetime.strptime(date_time + z, ORIGINAL_FTIME + "%z")
                .astimezone(datetime.timezone.utc)
                .replace(tzinfo=None)
            )
        return datetime.datetime.strptime(date_time, ORIGINAL_FTIME)

    i = exif_image(readable)
    try:
        t = getattr(i, "datetime_original", None)
        d = getattr(i, "image_description", None)
    except KeyError:
        # I guess if there's no metadata, it gets this
        # File "exif/_image.py", line 104, in __getattr__
        # KeyError: 'APP1'
        t = d = None
    return PKDict(date_time=_date_time(i, t), description=d)


def exif_set(readable, path=None, date_time=None, description=None):
    if path is None:
        path = readable
    assert path.ext == ".jpg"
    assert date_time or description
    e = exif_image(readable)
    if date_time is not None:
        e.datetime_original = date_time.strftime(ORIGINAL_FTIME)
    if description is not None:
        e.image_description = description
    path.write(e.get_file(), "wb")
    return date_time


def index_parse(path=None):
    def _parse(line):
        nonlocal path
        if not (i := _split(line)):
            pass
        elif not path.new(basename=i.name).exists():
            pkdlog("indexed image={} does not exist", i.name)
        elif i.name in rv:
            pkdlog(
                "duplicate image={} in {}; skipping desc={}",
                i.name,
                path,
                i.desc,
            )
        elif not KNOWN_EXT.search(i.name):
            pkdlog(
                "invalid ext image={} in {}; skipping desc={}",
                i.name,
                path,
                i.desc,
            )
        elif i.desc == MISSING_DESC:
            # assume everything will get identified
            pass
        else:
            # success
            return i
        return None

    def _split(line):
        l = line.rstrip()
        if l and not l.startswith("#"):
            if m := INDEX_LINE.search(l):
                return PKDict(zip(("name", "desc"), m.groups()))
            pkdlog("invalid line={}", l)
        return None

    rv = PKDict()
    if path is None:
        path = pykern.pkio.py_path()
    if path.check(dir=1):
        path = path.join("index.txt")
    if not path.exists():
        # No index so return empty PKDict so can be added to
        return rv
    with path.open("rt") as f:
        for l in f:
            if i := _parse(l):
                rv[i.name] = i.desc
    return rv


def index_update(image, desc):
    i = index_parse()
    i[image] = desc
    index_write(i)


def index_write(values):
    with open("index.txt", "w") as f:
        f.write("".join(k + " " + v + "\n" for k, v in values.items()))


def move_one(src, dst_root=None):
    e = src.ext.lower()
    if e == ".jpeg":
        e = ".jpg"
    # CreationDate is in timezone as is DateTimeOriginal but not for movies
    z = (
        ("-CreationDate", "-CreationDateValue", "-createdate", "-DateTimeOriginal")
        if MOVIE.search(src.basename)
        else ("-DateTimeOriginal",)
    )
    d = None
    for y in z:
        p = subprocess.run(
            ("exiftool", "-d", BASE_FTIME, y, "-S", "-s", src),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if p.returncode != 0:
            pkdlog("exiftool failed: path={} stderr={}", src, p.stderr)
            raise RuntimeError(f"unable to parse image={src}")
        if m := DATE_TIME_RE.search(str(p.stdout)):
            t = BASE_FMT.format(*m.groups())
            d = DIR_FMT.format(*m.groups())
            break
    if not d:
        d = datetime.datetime.fromtimestamp(src.mtime())
        t = d.strftime(BASE_FTIME)
        d = d.strftime(DIR_FTIME)
        pkdlog("use mtime: {} => {}", src, t)
    if dst_root:
        d = dst_root.join(d)
        pykern.pkio.mkdir_parent(d)
    else:
        d = pykern.pkio.py_path(".")
    f = d.join(t + e)
    if f == src:
        pkdlog("ignoring same name: {}", src, f)
        return
    pkdlog("src {}", src)
    if f.exists():
        for i in range(1, 10):
            if f.read("rb") == src.read("rb"):
                pkdlog("removing dup={} keep={}", src, f)
                src.remove(ignore_errors=True)
                return
            f = d.join("{}-{}{}".format(t, i, e))
            if not f.exists():
                break
        else:
            raise AssertionError("{}: exists".format(f))
    if src.dirname == f.dirname:
        _fix_index(src.dirpath(), src.basename, f.basename)
        pkdlog("mv {} {}", src.basename, f.basename)
    src.rename(f)
    pkdlog("dst {}", f)
    return f


def root():
    r = os.getenv("RNPIX_ROOT")
    assert r, "must set $RNPIX_ROOT"
    return pykern.pkio.py_path(r)


@contextlib.contextmanager
def user_lock():
    # Lock directories don't work within Dropbox folders, because
    # Dropbox uploads them and they can hang around after deleting here.
    lock_d = "/tmp/rnpix-lock-" + os.environ["USER"]
    lock_pid = os.path.join(lock_d, "pid")

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
                with open(lock_pid, "w") as f:
                    f.write(str(os.getpid()))
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                pid = _pid()
                if pid <= 0:
                    time.sleep(0.4)
                    continue
                if pid == _pid():
                    os.remove(lock_pid)
                    os.rmdir(lock_d)
        else:
            raise ValueError("{}: unable to create lock".format(lock_d))
        yield lock_d
    finally:
        if is_locked:
            os.remove(lock_pid)
            os.rmdir(lock_d)


def _fix_index(d, old, new):
    i = d.join("index.txt")
    if not i.exists():
        return
    r = []
    for l in i.read().split("\n"):
        if len(l.strip()) <= 0:
            continue
        if l.startswith(old):
            pkdlog("updating index: {} => {}", old, new)
            l = l.replace(old, new)
        r.append(l)
    i.write("\n".join(r) + "\n")

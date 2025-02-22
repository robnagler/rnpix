"""test dropbox_uploads

:copyright: Copyright (c) 2017-2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_move_all(monkeypatch):
    _move_all(monkeypatch)


def test_lock(monkeypatch):
    from pykern import pkunit, pkdebug, pkio
    import os

    def _create_lock(offset=0):
        # Copied code from user_lock
        d = pkio.py_path("/tmp/rnpix-lock-" + os.environ["USER"])
        d.ensure(dir=1)
        d.join("pid").write(str(os.getpid() + offset), ensure=True)
        return None

    with pkunit.pkexcept("unable to create lock", "should fail to create lock"):
        _move_all(monkeypatch, hook=_create_lock)

    _move_all(monkeypatch, hook=lambda: _create_lock(100000))


def _move_all(monkeypatch, hook=None):
    from pykern import pkunit
    from rnpix import unit

    def _image(uploads, index):
        return unit.image_create(uploads.join(f"2017_05_11 13_13_{i:02d}.jpg")).basename

    with pkunit.save_chdir_work() as d:
        photos = d.ensure("Dropbox", "Photos", "2017", "05-11", dir=True)
        monkeypatch.setenv("RNPIX_ROOT", str(photos.dirpath().dirpath()))
        uploads = d.ensure("Dropbox", "Camera Uploads", dir=True)
        if hook:
            hook()
        files = set()
        for i in range(3):
            files.add(_image(uploads, i))
        from rnpix.pkcli import move

        move.default_command(uploads)
        for f in map(photos.join, files):
            pkunit.pkok(f.check(), "file={} does not exist", f)

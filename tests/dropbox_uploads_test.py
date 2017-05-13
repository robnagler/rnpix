# -*- coding: utf-8 -*-
u"""test dropbox_uploads

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import pytest

def test_move_all(monkeypatch):
    _move_all(monkeypatch)


def test_lock(monkeypatch):
    from pykern import pkunit
    import os
    
    def _create_lock(d, offset=0):
        lock_pid = (d + '.lock').join('pid')
        lock_pid.write(str(os.getpid() + offset), ensure=True)
        return None

    with pkunit.pkexcept('unable to create lock', 'should fail to create lock'):
        _move_all(monkeypatch, hook=_create_lock)

    _move_all(monkeypatch, hook=lambda x: _create_lock(x, 100000))


def _move_all(monkeypatch, hook=None):
    from pykern import pkunit
    
    with pkunit.save_chdir_work() as d:
        photos = d.ensure('Dropbox', 'Photos', '2017', '05-11', dir=True)
        uploads = d.ensure('Dropbox', 'Uploads', dir=True)
        monkeypatch.setenv('HOME', d)
        if hook:
            hook(uploads)
        files = set()
        for i in range(3):
            f = '2017_05_11_p{}.jpg'.format(i)
            files.add(f)
            uploads.ensure(f)
        from rnpix.pkcli import dropbox_uploads
        dropbox_uploads.default_command(str(uploads.join('any-file')))
        for f in files:
            assert photos.join(f).check(), \
                '{}: does not exist'.join(f)


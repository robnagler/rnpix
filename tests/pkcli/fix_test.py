"""test fix.date_time

:copyright: Copyright (c) 2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_date_time():
    from pykern import pkunit, pkdebug, pkio
    from pykern.pkcollections import PKDict
    from pykern.pkunit import pkeq
    from rnpix import unit, common
    from rnpix.pkcli import fix
    import exif

    def _expect(pwd):
        p = pwd.ensure("2006", "10-12", dir=True)
        with pkio.save_chdir(p):
            pkunit.pkok(
                d := common.date_time_parse(p.join("x.jpg")),
                "path={} date parsing failed",
                p,
            )
            return _index_create(
                PKDict(
                    {
                        d: _image(p, "anything"),
                        d.replace(second=1): _image(p, "1"),
                        d.replace(second=2): _image(p, "2006-10-12-2"),
                        d.replace(hour=11, minute=12, second=13): _image(
                            p, "2006-10-12-11.12.13"
                        ),
                    }
                )
            )

    def _index_create(images):
        common.index_write(PKDict({v.path.basename: v.desc for v in images.values()}))
        return images

    def _image(path, base):
        p = path.new(dirname=path, purebasename=base, ext=".jpg")
        p.write_binary(unit.image_create_handle(p.basename).read())
        return PKDict(path=p, desc=base + " sometag")

    def _paths(expect):
        return tuple(map(lambda x: x.path, expect.values()))

    with pkunit.save_chdir_work() as d:
        e = _expect(d)
        pkeq(
            tuple(sorted(_paths(e))),
            fix.exif_data(*_paths(e)),
            "verify all files changed",
        )
        for k, v in e.items():
            a = common.exif_parse(v.path)
            pkeq(k, a.date_time, "date mismatch path={}", v)
            pkeq(v.desc, a.description, "desc mismatch path={}", v)
        pkeq(
            tuple(),
            fix.exif_data(*_paths(e)),
            "files should not change a second time",
        )

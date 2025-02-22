"""test fix.date_time

:copyright: Copyright (c) 2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_date_time():
    from pykern import pkunit, pkdebug
    from pykern.pkcollections import PKDict
    from rnpix import unit, common
    from rnpix.pkcli import fix
    import exif

    def _expect(pwd):
        p = pwd.ensure("2006", "10-12", dir=True)
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
                        p, "2006-10-12-11:12:13"
                    ),
                }
            )
        )

    def _index_create(images):
        common.index_write(PKDict(
            {v.path.basename: v.desc for v in images.values()}
        ))
        return images

    def _image(path, base):
        p = path.new(dirname=path, purebasename=base, ext=".jpg")
        p.write_binary(unit.image_create_handle(p.basename).read())
        return PKDict(path=p, desc=base + " sometag")

    with pkunit.save_chdir_work() as d:
        e = _expect(d)
        pkunit.pkeq(
            tuple(sorted(e.values())),
            fix.exif_data(*list(e.values())),
            "verify all files changed",
        )
        for k, v in e.items():
            a = common.exif_parse(v)
            pkunit.pkeq(k, a.date_time "exif date mismatch path={}", v)
            pkunit.pkeq(, a.date_time "exif date mismatch path={}", v)
        pkunit.pkeq(
            tuple(),
            fix.date_time(*list(e.values())),
            "files should not change a second time",
        )

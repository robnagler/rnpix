"""test fix.date_time

:copyright: Copyright (c) 2025 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_date_time():
    from pykern import pkunit
    from pykern.pkcollections import PKDict
    from rnpix import unit, common
    from rnpix.pkcli import fix

    def _expect(pwd):
        p = pwd.ensure("2006", "10-12", dir=True)
        d = common.date_time_parse(p)
        return PKDict(
            {
                d: _image(p, "anything"),
            }
        )

    def _image(path, base):
        p = path.new(dirname=path, purebasename=base, ext=".jpg")
        unit.image_create(p)
        return p

    with pkunit.save_chdir_work() as d:
        e = _expect(d)
        a = fix.date_time(*list(e.values()))
        verify the time
        pkunit.pkeq(("anything",), tuple(map(lambda x: x.purebasename, a)))

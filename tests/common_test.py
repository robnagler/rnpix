"""test common

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_index_parse():
    from pykern import pkio, pkunit
    from pykern.pkcollections import PKDict
    from pykern.pkunit import pkeq
    from rnpix import common

    with pkunit.save_chdir_work() as d:
        d.join("index.txt").write(
            """x.jpg 123
1.png   a b c
# comment
"""
        )
        d.join("x.jpg").ensure(file=1)
        d.join("1.png").ensure(file=1)
        pkeq(PKDict({"x.jpg": "123", "1.png": "a b c"}), common.index_parse())
    pkeq(PKDict({"x.jpg": "123", "1.png": "a b c"}), common.index_parse(d))

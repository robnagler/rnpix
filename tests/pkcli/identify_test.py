"""test identify

:copyright: Copyright (c) 2022 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_need_to_index(monkeypatch):
    from pykern import pkunit, pkio, pkjson
    from pykern.pkcollections import PKDict
    from pykern.pkdebug import pkdp
    from rnpix.pkcli import identify
    import os

    for _ in pkunit.case_dirs():
        for d in pkio.sorted_glob("*"):
            with pkio.save_chdir(d):
                n = identify.need_to_index()
                pkjson.dump_pretty(n, filename="res.json")
                os.chdir(n[0])
                i = pkio.read_text("input.txt").split("\n")
                with monkeypatch.context() as m:
                    m.setattr("builtins.input", lambda x: i.pop(0))
                    m.setattr("subprocess.check_call", lambda x: None)
                    identify.add_to_index()

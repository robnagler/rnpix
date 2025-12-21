""":mod:`rnpix` package

:copyright: Copyright (c) 2024 Robert Nagler.  All Rights Reserved.
:license: https://www.apache.org/licenses/LICENSE-2.0.html
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("rnpix")
except importlib.metadata.PackageNotFoundError:
    # We only have a version once the package is installed.
    pass

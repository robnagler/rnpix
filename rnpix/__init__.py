""":mod:`rnpix` package

:copyright: Copyright (c) 2024 Robert Nagler.  All Rights Reserved.
:license: https://www.apache.org/licenses/LICENSE-2.0.html
"""

import pkg_resources

try:
    # We only have a version once the package is installed.
    __version__ = pkg_resources.get_distribution("rnpix").version
except pkg_resources.DistributionNotFound:
    pass

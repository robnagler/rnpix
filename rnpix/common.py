# -*- coding: utf-8 -*-
u"""Commond definitions

:copyright: Copyright (c) 2017 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import re

IMAGE_SUFFIX = re.compile(
    '\.(mp4|jpg|png|tif|gif|pcd|psd|mpg|pdf|mov|jpg|avi|thm|jpeg)$',
    flags=re.IGNORECASE,
)

MOVIE_SUFFIX = re.compile(
    r'\.(mp4|mov|mpg|avi)$',
    flags=re.IGNORECASE,
)

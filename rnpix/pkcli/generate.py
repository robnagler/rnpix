#!/usr/bin/env python
from __future__ import print_function
import cgi
import os
import os.path
import glob
import re

# for f in *.jpg; do convert -resize x200 -quality 50% $f t\
#    /$f; done
# https://github.com/cebe/js-search

head = """<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" type="text/css" href="../../static/pix.css">
</head>
<body class="robnagler_pix>
"""

tail = """</body>
</html>
"""

dirs = sorted(list(glob.glob('[0-9][0-9]-[0-9][0-9]')))
for d in dirs:
    os.chdir(d)
    try:
        if not os.path.exists('index.txt'):
            continue
        middle = ''
        with open('index.txt') as f:
            lines = list(f)
        for l in lines:
            m = re.search(r'^(.+?):?\s+(.+)', l)
            if not m:
                print(os.getcwd() + ': ERR ' + l)
                continue
            middle += ("<figure><img src='t/{i}' onclick='this.src=" + '"{i}"' + "' /><figcaption>{c}</figcaption></figure></a>\n").format(i=m.group(1), c=cgi.escape(m.group(2)))
        open('index.html', 'w').write(head + middle + tail)
    finally:
        os.chdir('..')
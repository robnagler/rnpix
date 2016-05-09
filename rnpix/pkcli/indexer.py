# -*- coding: utf-8 -*-
u"""?

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

from pykern import pkio
import json
import os.path
import py.path
import re
import string

_DIR_RE = re.compile(r'(.+)/(\d{4})/(\d\d)-(\d\d)$')

_LINE_RE = re.compile(r'^(.+?):?\s+(.+)')

_DELIMITER_RE = re.compile(r'\W+')

_STOP_WORDS = set((
    # default lucene http://stackoverflow.com/questions/17527741/what-is-the-default-list-of-stopwords-used-in-lucenes-stopfilter
    'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by',
    'for', 'if', 'in', 'into', 'is', 'it',
    'no', 'not', 'of', 'on', 'or', 'such',
    'that', 'the', 'their', 'then', 'there', 'these',
    'they', 'this', 'to', 'was', 'will', 'with',
)) | set(string.lowercase) | set(string.digits)

def default_command():
    res = _search_and_parse()
    with open('rnpix-index.js', 'w') as f:
        f.write(_json(res))


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        return super(_JSONEncoder, self).default(self, obj)


def _add_words(words, file_index, new):
    for w in new:
        if not w in words:
            words[w] = set()
        words[w].add(file_index)


def _index_parse(filename, file_index):
    image = None
    words = set()
    title = ''
    title_done = False
    with open(filename) as f:
        for l in f:
            if l.startswith('#'):
                continue
            m = _LINE_RE.search(l)
            if not m:
                raise ValueError('{}: invalid line in {}'.format(l, filename))
            if not image:
                image = m.group(1)
            for w in _index_parse_line(m.group(2)):
                words.add(w)
                if len(title) < 100:
                    title += ' ' + w
                else:
                    title_done = True
            if not title_done:
                title += ';'
    assert image, '{}: no image'.format(filename)
    return words, image, title


def _index_parse_line(line):
    for w in _DELIMITER_RE.split(line.lower()):
        if len(w) and not w in _STOP_WORDS:
            yield w

def _json(res):
    return 'rnpix.index=' + json.dumps(
        res,
        cls=_JSONEncoder,
        separators=(',',':'),
    ) + ';\n'


def _search_and_parse():
    files = list(pkio.walk_tree('.', file_re=r'index.txt$'))
    files.reverse()
    res = {
        'images': [],
        'links': [],
        'titles': [],
        'words': {},
    }
    for f, fi in zip(files, xrange(len(files))):
        s = _DIR_RE.search(f.dirname)
        assert s, '{}: non-date dirname'.format(f)
        root = py.path.local(s.group(1))
        y, m, d = s.group(2, 3, 4)
        _add_words(res['words'], fi, [y, y + m, y + m + d])
        w, i, t = _index_parse(str(f), fi)
        res['links'].append(root.bestrelpath(py.path.local(f.dirname)))
        res['images'].append(_thumb(i))
        res['titles'].append('{}/{}/{}{}'.format(m, d, y, t))
        _add_words(res['words'], fi, w)
    return res


def _thumb(image):
    return re.sub(r'\.\w+$', '', image)



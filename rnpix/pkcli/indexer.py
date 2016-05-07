# -*- coding: utf-8 -*-
u"""?

:copyright: Copyright (c) 2016 Robert Nagler.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

import re
from pykern import pkio

_DIR_RE = re.compile(r'/(\d{4})/(\d\d)-(\d\d)$')

_LINE_RE = re.compile(r'^(.+?):?\s+(.+)')

_DELIMITER_RE = re.compile(r'\W+')

_STOP_WORDS = [
    # default lucene http://stackoverflow.com/questions/17527741/what-is-the-default-list-of-stopwords-used-in-lucenes-stopfilter
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by',
    'for', 'if', 'in', 'into', 'is', 'it',
    'no', 'not', 'of', 'on', 'or', 'such',
    'that', 'the', 'their', 'then', 'there', 'these',
    'they', 'this', 'to', 'was', 'will', 'with'
]
_STOP_WORDS = dict(zip(_STOP_WORDS, xrange(len(_STOP_WORDS))))

def default_command():
    files, words, images, titles = _search_and_parse()


def _add_words(words, file_index, new):
    for w in new:
        if not w in words:
            words[w] = set()
        words[w].add(file_index)


def _search_and_parse():
    files = list(pkio.walk_tree('.', file_re=r'index.txt$'))
    files.reverse()
    words = {}
    images = {}
    titles = {}
    for f, fi in zip(files, xrange(len(files))):
        s = _DIR_RE.search(f.dirname)
        assert s, '{}: non-date dirname'.format(f)
        y, m, d = s.group(1, 2, 3)
        _add_words(words, fi, [y, y + m, y + m + d])
        w, i, t = _index_parse(str(f), fi)
        images[fi] = i
        titles[fi] = '{}/{}/{}{}'.format(m, d, y, t)
        _add_words(words, fi, w)
    return files, words, images, titles


def _index_parse(filename, file_index):
    image = None
    words = set()
    title = ''
    with open(filename) as f:
        for l in f:
            m = _LINE_RE.search(l)
            if not m:
                raise ValueError('{}: invalid line in {}'.format(l, filename))
            if not image:
                image = m.group(1)
            for w in _index_parse_line(m.group(2)):
                words.add(w)
                if len(title) < 100:
                    title += ' ' + w
    assert image, '{}: no image'.format(filename)
    return words, image, title


def _index_parse_line(line, words):
    for w in _DELIMITER_RE.split(line.lower()):
        if len(w) and not w in _STOP_WORDS:
            yield w

def _print_index_js():

### Photo Library Tools

For a demo, visit [rnpix.github.io](https://rnpix.github.io).

The photo library is organized into "day" directories of the form
`YYYY/MM-DD/*.{jpg,mov,...}`. In each day directory, `index.txt`
contains:

```text
foo.jpg Some description for foo on one line
bar.mov A movie of something
```

The file may have comments with a `#` starting on the first character. (Historical version allows a `:` after the image name.)

The tools search `YY/MM-DD` directories to create `index.txt` and uses it to create a searchable, static HTML tree:

1. [identify](rnpix/pkcli/identify.py) appends to `index.txt` from the images in a day directory, prompting the user for each unidentified image.
2. [generate](rnpix/pkcli/generate.py) reads `index.txt` to create `index.html` and thumbnail directories `50` (pixel) and `200`, which are referenced in `index.html`
3. [indexer](rnpix/pkcli/indexer.py) reads `index.txt` to create `rnpix-index.js`, which is read by [rnindex](rnpix/package_data/static/rnindex.js) to find images by their description.
4. [fix](rnpix/pkcli/fix.py) reads `index.txt` and images in directory, and verifies and fixes the format.

#### Acknowledgements

Thanks to the excellent [js-search](https://github.com/cebe/js-search) by [Carsten Brandt](http://cebe.cc/about). It was first transliterated from the PHP
to Python, and then rewritten to match the picture indexing problem,
which was significantly different from the general HTML problem `js-search`
solves. I wouldn't have gotten the idea of how to implement a search
engine in Javascript without Carsten's project.

The rest of the code is all mine and evolved over a couple of decades
from a collection of simple Perl programs to be transformed this
year to Python.

#### License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2016 Robert Nagler.  All Rights Reserved.

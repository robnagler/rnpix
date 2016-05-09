var rnpix = {
    search: function(query) {
	return rnpix.tokenize(query)
            .reduce(
                function(files, word) {
                    if (! (word in rnpix.index.words)) {
                        return [];
                    }
                    var f = rnpix.index.words[word];
                    res = files.length ? _.intersection(files, f)
                        : f;
                    return res;
                },
                []
            )
            .map(
                function(f) {
                    return {
                        title: rnpix.index.titles[f],
                        link: rnpix.link(f),
                        image: rnpix.image(f)
                    };
                }
            ).toArray()
            .value();
    },

    image: function(fileIndex) {
        return rnpix.index.links[fileIndex]
            + '/50/'
            + rnpix.index.images[fileIndex]
            + '.jpg';
    },

    link: function(fileIndex) {
        return rnpix.index.links[fileIndex] + '/index.html'
    },

    stopWords: [
        // default lucene http://stackoverflow.com/questions/17527741/what-is-the-default-list-of-stopwords-used-in-lucenes-stopfilter
        "an", "and", "are", "as", "at", "be", "but", "by",
        "for", "if", "in", "into", "is", "it",
        "no", "not", "of", "on", "or", "such",
        "that", "the", "their", "then", "there", "these",
        "they", "this", "to", "was", "will", "with",
    ],
    
    tokenize: function(string) {
        return _.chain(string.toLowerCase().split(/\W+/))
            .filter(function(word) {
                return word.length > 1 && !(word in rnpix.stopWords);
            })
            .uniq();
    }
};

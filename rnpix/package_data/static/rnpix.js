var rnpix = {
    search: function(query) {
	var words = rnpix.tokenizeString(query);
	var result = [];
	if (!words.length) {
	    return result
	}
        for (var w in words) {
            var i = rnpix.index[word]
	result = rnpix.searchForWords(words);
	var res = [];
	for (var i in result) {
	    res.push(result[i]);
	}
	return res;
    },

    searchForWords: function(words) {
	var result = []
        _.chain(words)
            .filter(
	words.forEach(function(word) {
	    if (!i) {
                return;
            }
	    i.forEach(function(file) {
		if (result[file.f]) {
			result[file.f].weight *= file.w * word.w;
		    } else {
			result[file.f] = {
			    file: rnpix.files[file.f],
			    weight: file.w * word.w
			};
		    }
		});
	    }
	});
	return result;
    },

    stopWords: [
        // default lucene http://stackoverflow.com/questions/17527741/what-is-the-default-list-of-stopwords-used-in-lucenes-stopfilter
        "a", "an", "and", "are", "as", "at", "be", "but", "by",
        "for", "if", "in", "into", "is", "it",
        "no", "not", "of", "on", "or", "such",
        "that", "the", "their", "then", "there", "these",
        "they", "this", "to", "was", "will", "with"
    ],
    
    tokenizeString: function(string) {
        return _.chain(string.toLowerCase().split(/\W+/))
            .filter(function(word) {
                return !(word in rnpix.stopWords);
            })
            .uniq()
            .value();
    }
};

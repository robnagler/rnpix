$(document).ready(function() {
    $('#searchbox').on(
        "keyup",
        function() {
            $('#results').html(
                _.chain(rnpix.search($(this).val()))
                    .first(20)
                    .reduce(
                        function(memo, elem) {
                            return '<li><a href="' + elem.link + '">'
                                + _.escape(elem.title) + '</a></li>';
                        },
                        ''
                    )
                    .value()
            );
        }
    )
});

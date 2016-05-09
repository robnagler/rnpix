$(document).ready(function() {
    var results = $('<div>', {
        class: 'rnpix_search_results'
    });
    var input = $('<input>', {
        type: 'text',
        value: '',
        placeholder: 'Search...'
    })
    $('.rnpix_search_widget').append(input).append(results);
    input.focus()
        .on("keyup", function() {
            results.html('')
            _.chain(rnpix.search($(this).val()))
                .first(100)
                .each(function(e) {
                    results.append(
                        $('<a>', {href: e.link})
                            .append(
                                $('<figure>')
                                    .append(
                                        $('<span>', {class: 'rnpix_image'})
                                            .append($('<img>', {src: e.image})))
                                    .append($('<figcaption>', {html: _.escape(e.title)}))
                            )
                    );
                });
    });
});

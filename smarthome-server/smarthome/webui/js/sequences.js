'use strict';

updates = updates.concat([
    [updateSequences, 15, 0],
]);

function updateSequences() {
    $.get(apiURL + "sequences", function(data) {
        console.log("POET");
        console.log(data);
            $('#running-seqs .sequence').remove();

            if (Object.keys(data).length > 0)
                $('#running-seqs .text-center').hide();
            else
                $('#running-seqs .text-center').show();

            for (var i in data) {
                var el = $('#running-seqs').append(
                    '<p class="sequence" data-id="'+data[i]["id"]+'">' +
                        '&ndash; ' + data[i]["name"] + ' <i class="fa fa-times-circle-o"></i>' +
                    '</p>');
            }

        $('#running-seqs i').on("click", function () {
            $.ajax(apiURL + 'sequences/'+$(this).parent().attr('data-id'), {
                method: 'DELETE',
                success: function () {
                    updateSequences();
                }
            });
        });
    });
}

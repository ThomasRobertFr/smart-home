'use strict';

updates = updates.concat([
    [updateSequences, 25, 0],
]);

function updateSequences() {
    $.get(apiURL + "sequence_groups", function(data) {
        $('#running-seqs .sequence').remove();

        if (Object.keys(data).length > 0)
            $('#running-seqs .text-center').hide();
        else
            $('#running-seqs .text-center').show();

        for (var i in data) {
            var el = $('#running-seqs').append(
                '<p class="sequence" data-id="'+data[i]["id"]+'">' +
                    '<i class="fad fa-angle-right"></i> ' + data[i]["name"] +
                    ' <span class="stop-sequence"><i class="fad fa-times-circle"></i></span>' +
                '</p>');
        }

        $('#running-seqs .stop-sequence').on("click", function () {
            $.ajax(apiURL + 'sequence_groups/'+$(this).parent().attr('data-id'), {
                method: 'DELETE',
                success: function () {
                    updateSequences();
                }
            });
        });
    });

    // UPDATE THE SWITCHES SEQUENCES DISPLAY
    $.get(apiURL + "sequences", function(data) {
        $('.switch .sequence-running').addClass("hide");
        for (var i in data) {
            $('.switch[data-idx='+data[i].device_idx+'] .sequence-running').removeClass("hide");
            $('.switch[data-idx='+data[i].device_idx+'] .sequence-running').data("seq-id", data[i].id);
        }
    });
}


$(document).ready(function() {
    $('.switch .sequence-running').click(function () { vibrate();
        $(this).addClass("hide");
        var el = $(this).parents(".switch");
        var idx = el.data('idx');
        $.ajax(apiURL + 'sequences/'+$(this).data("seq-id"), {
            method: 'DELETE'
        });
    });
});

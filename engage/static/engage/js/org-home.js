$(function() {
    // initialize our glyph checkboxes
    var boxes = $("td.check");
    boxes.each(function() {
        var list_input = $(this).children().children("input[type='checkbox']");
        if (list_input[0].checked) {
            $(this).addClass("checked");
        } else {
            $(this).removeClass("checked");
        }
    });
});

$(function() {
    // update the glyph checkbox on click

    $("td.check .glyph").on('click', function(){
        var cell = $(this).parent("td.check");
        var ipt = cell.children().children("input[type='checkbox']");

        if (!cell.hasClass("checked")) {

            cell.parent().children('td.check').removeClass('checked');
            cell.parent().children('td.check').children().children("input[type='checkbox']").attr('checked', false);

            cell.addClass("checked");
            //ipt.attr('checked', true);
        }

    });
});

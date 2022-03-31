function posterize(href) {
    var url = $.url(href);
    $("#posterizer").attr("action", url.attr("path"));
    for (var key in url.param()){
        $("#posterizer").append("<input type='hidden' name='" + key + "' value='" + url.param(key) + "'></input>");
    }
    $("#posterizer").submit();
}

function handlePosterize(ele) {
    posterize(ele.getAttribute('href'));
}

function removalConfirmation(removal, buttonName) {

    var modal = document.querySelector("#general-delete-confirmation");
    modal.classList.remove("hidden");

    // set modal deets
    var title = document.querySelector('.' + removal + ' > .title').innerHTML;
    var body = document.querySelector('.' + removal + ' > .body').innerHTML;

    modal.header = title;
    modal.querySelector('.confirmation-body').innerHTML = body;

    modal.open = true;

    modal.addEventListener("temba-button-clicked", function(event){
        if(!event.detail.button.secondary) {
            var ele = document.querySelector('#' + removal + '-form');
            handlePosterize(ele);
        }
        modal.open = false;

        // clear our listeners
        modal.outerHTML = modal.outerHTML;
    });
}

function formatContact(item) {
    if (item.text.indexOf(" (") > -1) {
        var name = item.text.split("(")[0];
        if (name.indexOf(")") == name.length - 1) {
            name = name.substring(0, name.length - 1);
        }
        return name;
    }
    return item.text;
}

function createContactChoice(term, data) {
    if ($(data).filter(function() { return this.text.localeCompare(term)===0; }).length===0) {
        if (!isNaN(parseFloat(term)) && isFinite(term)) {
            return {id:"number-" + term, text:term};
        }
    }
}

String.prototype.sprintf = function() {
    return [...arguments].reduce((p,c) => p.replace(/%s/,c), this);
}

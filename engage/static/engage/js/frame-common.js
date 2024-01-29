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

function refresh(onSuccess, forceReload){
    let url = params; //from haml
    if ( url === '' ) {
        url = '?';
    } else {
        const url_params = new Proxy(new URLSearchParams(window.location.search), {
          get: (searchParams, aProp) => searchParams.get(aProp),
        });
        if ( url_params.get('norefresh') ) {
            return;
        }
        const page_num = url_params.get('page');
        if ( page_num ) {
            url += "page="+page_num;
        }
    }

    url += '&ts=' + new Date().getTime() + "&refresh=" + refreshTimeout;

    document.dispatchEvent(new Event("temba-refresh-begin"));
    fetchPJAXContent(url, '#pjax', {
        onSuccess: function() {
            if ( onSuccess ) {
                onSuccess();
            }
            document.dispatchEvent(new Event("temba-refresh-complete"));
            //do not decay refresh rate
            //refreshTimeout = Math.floor(refreshTimeout * 1.1)
            scheduleRefresh();
        },
        shouldIgnore: function() {
            if ( forceReload ) {
                return false;
            }
            const pjax = document.querySelector("#pjax");
            if ( pjax ) {
                return eval(document.querySelector("#pjax").dataset.noPjax);
            }
            return true;
        },
        onIgnore: function() {
            const pjax = document.querySelector("#pjax");
            if ( pjax ) {
                scheduleRefresh();
            }
        }
    });
}

document.addEventListener("temba-redirected", function(event){
  document.location.href = event.detail.url;
});

const btnSound = document.getElementById('btnSound');
btnSound.addClass('hidden');
function playSound() {
    const theId = btnSound.dataset.sound_id || '37';
    btnSound.audioFile = new Audio(`engage/audio/notify_${theId}.mp3`);
    btnSound.audioFile.loop = true;
    btnSound.audioFile.play();
}
function performSound( aID ){
    if ( aID ) {
        btnSound.dataset.sound_id = aID;
    }
    btnSound.click();
}
function stopSound(){
    btnSound.audioFile.pause();
    btnSound.audioFile.currentTime = 0;
}

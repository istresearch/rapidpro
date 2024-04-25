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
        if ( url_params.norefresh ) {
            return;
        }
        const page_num = url_params.page;
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

const theBusySpinner = $('#busy-spinner');
function showSpinner() {
    if ( window.app_spin_count === 0 ) {
        window.app_spin_count = 1;
        theBusySpinner.removeClass('hidden');
    } else {
        window.app_spin_count += 1;
    }
}
function hideSpinner() {
    if ( window.app_spin_count > 1 ) {
        window.app_spin_count -= 1;
    } else {
        window.app_spin_count = 0;
        theBusySpinner.addClass('hidden');
    }
}
function resetSpinner() {
    window.app_spin_count = 1;
    hideSpinner();
}
//if using the Back button to return to a page where the spinner was shown before navigating away, handle it
window.addEventListener('pageshow', function (e) {
    //typescript would need: (performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming).type
    if ( e.persisted || performance.getEntriesByType("navigation")[0].type === 'back_forward' ) {
        resetSpinner();
    }
});

const btnSound = document.getElementById('btnSound');
btnSound.style.visibility = 'hidden';
function playSound() {
    const theId = btnSound.dataset.sound_id || '37';
    if ( btnSound && btnSound.audioFileSrc !== '/sitestatic/engage/audio/notify_'+theId+'.mp3' ) {
        btnSound.audioFileSrc = '/sitestatic/engage/audio/notify_'+theId+'.mp3';
        btnSound.audioFile = new Audio(btnSound.audioFileSrc);
        btnSound.audioFile.loop = true;
    }
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

function putToastInToaster(type, content, delay=7000) {
    if (!content) { return; } //if nothing to display, exit right away.
    const bUseAlert = ( !$().toast );
    const toast = document.createElement('div');
    toast.setAttribute('id', 'toast-' + Date.now());
    toast.classList.add('toast', 'fade', 'in', 'alert-dismissible', type);
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('delay', ''+Math.max(delay, 7000));

    let btnClose = document.createElement('button');
    btnClose.classList.add('p-2', 'ml-auto');
    btnClose.setAttribute('aria-label', 'Close');
    btnClose.setAttribute('data-dismiss', (bUseAlert) ? 'alert' : 'toast');
    let btnCloseText = document.createElement('span');
    //btnCloseText.classList.add('', 'true');
    btnCloseText.setAttribute('aria-hidden', 'true');
    btnCloseText.innerHTML = '&times;';
    btnClose.addEventListener('click', (e) => {
        document.getElementById(toast.getAttribute('id')).remove();
    });
    btnClose.append(btnCloseText);

    let toastBody = document.createElement('div');
    toastBody.classList.add('toast-body', type, 'flex', 'flex-row');
    if ( content.startsWith('<') ) {
        toastBody.innerText = content;
    } else {
        let toastBodyText = document.createElement('div');
        toastBodyText.classList.add('msg');
        toastBodyText.style.alignContent = 'center';
        toastBodyText.append(document.createTextNode(content));
        toastBody.append(toastBodyText);
    }
    toastBody.append(btnClose);

    toast.appendChild(toastBody);
    $('#toaster').append(toast);
    if ( bUseAlert ) {
        toast.classList.add('show');
        if ( delay ) {
            setTimeout(() => {
                toast.addEventListener("transitionend", (event) => {
                    toast.remove();
                });
                toast.style.opacity = '0';
            }, delay);
        }
    } else {
        let el = $('#'+toast.getAttribute('id'));
        el.toast('show');
    }
}

function wireupClearTextWidgets() {
    const theInputs = $('input[type="text"][class*=" has-clear-text"]');
    theInputs.on('input propertychange', () => {
        const $this = $(this);
        const visible = Boolean($this.val());
        $this.siblings('.form-control-clear').toggleClass('hide-me', !visible);
    }).trigger('propertychange');

    $('.form-control-clear').click(() => {
        $(this).siblings('input[type="text"]').val('')
            .trigger('propertychange').focus();
    });
}

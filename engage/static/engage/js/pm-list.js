let elListButtons;
function handleRowSelection(checkbox) {
    const row = checkbox.closest("tr");
    if (row) {
        if (checkbox.checked) {
            row.classList.add('checked');
            elListButtons.classList.add('visible');
        } else {
            row.classList.remove('checked');
            // if nothing else is also checked, hide bulk action buttons
            if ( !document.querySelector('tr.checked') ) {
                elListButtons.classList.remove('visible');
            }
        }
    }
}

function handleRowClicked(event) {
    if (event.target.tagName !== "TEMBA-CHECKBOX") {
      const row = event.target.closest('tr');
      const uuid = row.getAttribute("data-object-uuid");
      gotoLink("/pm/read/" + uuid + "/");
    }
}

function handleSortOnHeader(e) {
    let searchParams = new URLSearchParams(window.location.search);
    const params = new Proxy(searchParams, {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    let sortOn = params._order;
    let bSortDirAsc = !sortOn.startsWith('-');
    let theSortField = (bSortDirAsc) ? sortOn : sortOn.slice(1);
    let theNewSortField = e.target.id.substr(e.target.id.indexOf("-")+1);

    if ( theNewSortField === theSortField ) {
        theNewSortField = (bSortDirAsc ? '-' : '') + theNewSortField;
    }
    searchParams.set('sort_on', theNewSortField);
    window.location.search = searchParams.toString();
}

$(document).ready(function(){
    elListButtons = document.querySelector('.list-buttons-container');
    $("th.header").click(handleSortOnHeader);
});

function getCheckedData(data2get='object-uuid') {
    let checkedUuids = [];
    const checks = $('.object-row.checked');
    for (let i = 0; i < checks.length; i++) {
        checkedUuids.push($(checks[i]).data(data2get));
    }
    return checkedUuids;
}

function postReq( params ) {
    const request = {
        url: params.url,
        type: params.data ? 'POST' : 'GET',
        data: params.data,
        headers: params.headers,
        success: params.success,
        error: params.error,
    }
    return $.ajax(request);
}

function wireupActionPurge() {
    const menuitemPurge = document.querySelector("#action-purge");
    const dlgPurge = document.querySelector("#purge-confirmation");
    if ( menuitemPurge && dlgPurge ) {
        menuitemPurge.addEventListener("click", function(e) {
            dlgPurge.classList.remove("hide");
            dlgPurge.open = true;
        });

        dlgPurge.addEventListener("temba-button-clicked", function(e) {
            if (!e.detail.button.secondary) {
                showSpinner();
                let objList = getCheckedData('object-id');
                Promise.all(objList.map((id) => {
                    return postReq({
                        url: `/channels/purge/pm_service/${id}`,
                        success: (resp) => {
                            putToastInToaster('alert-success', resp);
                        },
                    });
                })).then(
                    () => {
                        hideSpinner();
                    },
                    () => {
                        hideSpinner();
                    }
                );
            }
            dlgPurge.open = false;
        });
    }
}

function wireupActionRename() {
    const menuitem = document.querySelector("#action-rename");
    const btnSubmit = document.querySelector("#btn-submit-rename");
    if ( menuitem && btnSubmit ) {
        btnSubmit.addEventListener("click", function(e) {
            showSpinner();
            const inputNameFormat = document.querySelector('#pm-name-format');
            let theNameFormat = inputNameFormat.value;
            if ( !theNameFormat ) {
                theNameFormat = '{{device_id}} {{pm_scheme}}';
            }
            let objList = getCheckedData('object-id');
            Promise.all(objList.map((id) => {
                return postReq({
                    url: `/pm/rename_channels/${id}/`,
                    data: {name_format: theNameFormat},
                }).then((resp) => {
                    putToastInToaster('alert-success', resp.msg);
                    const rowDeviceName = $('tbody').find(`tr[data-object-id='${resp.id}'] > td > a`);
                    if ( rowDeviceName ) {
                        rowDeviceName.text(resp.name);
                    }
                }, (resp) => {
                    putToastInToaster('alert-warning', resp.msg);
                });
            })).then(
                () => {
                    hideSpinner();
                },
                () => {
                    hideSpinner();
                }
            );
        });
    }
}

window.addEventListener('DOMContentLoaded', function(e) {
    wireupActionPurge();
    wireupActionRename();
});

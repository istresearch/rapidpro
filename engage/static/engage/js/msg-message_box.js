function handleRowClick(uuid) {
    gotoLink("/contact/read/" + uuid + "/");
}

function handleAddLabelClicked() {
    document.getElementById("create-label-modal").open = true;
}

var btnExportMsgs = null;
var btnDelete = null;
var dlgDelConfirm = null;

/**
 * pjax is used to reload parts of the DOM occationally, call this function
 * both when DOM is first ready and whenever pjax finishes its DOM changes.
 * NOTE: DO NOT PLACE .addEventListener() for elements outside of the pjax
 *       subtree else they will get duplicated after every pjax refresh!
 */
function handlePjaxAreaListeners() {
    btnExportMsgs = document.querySelector('#export-messages');
    if ( btnExportMsgs ) {
        let theOrigRemoveAttribute = btnExportMsgs.removeAttribute;
        btnExportMsgs.removeAttribute = (key) => {
            if ( key === 'open' && btnExportMsgs.hasAttribute('open') ) {
                window.location.reload(true);
            }
            theOrigRemoveAttribute.call(btnExportMsgs, key);
        };
    }

    btnDelete = document.querySelector(".object-btn-delete");
    if ( btnDelete && dlgDelConfirm ) {
        btnDelete.addEventListener("click", function(e) {
            if ( !dlgDelConfirm.mConfirmed ) {
                e.preventDefault();
                e.stopPropagation();
                dlgDelConfirm.open = true;
                dlgDelConfirm.classList.remove("hide");
            }
            else {
                // reset back to un-confirmed to prepare for next time it's clicked.
                dlgDelConfirm.mConfirmed = false;
            }
        });
    }

}

$(document).ready(function() {
    dlgDelConfirm = document.querySelector("#delete-confirmation");
    if ( dlgDelConfirm ) {
        dlgDelConfirm.mConfirmed = false;
        dlgDelConfirm.addEventListener("temba-button-clicked", function(e) {
            dlgDelConfirm.mConfirmed = ( e.detail.button.name === e.target.primaryButtonName );
            dlgDelConfirm.classList.add("hide");
            dlgDelConfirm.open = false;
            if ( dlgDelConfirm.mConfirmed && btnDelete ) {
                setTimeout(function() {
                    btnDelete.click();
                });
            }
        });
    }

    handlePjaxAreaListeners();
});
// pjax standard events replaced with custom ones, because of course custom ones were needed.
document.addEventListener('temba-pjax-complete', handlePjaxAreaListeners, false);

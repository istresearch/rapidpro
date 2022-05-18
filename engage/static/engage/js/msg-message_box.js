function handleRowClick(uuid) {
    gotoLink("/contact/read/" + uuid + "/");
}

function handleAddLabelClicked() {
    document.getElementById("create-label-modal").open = true;
}

$(document).ready(function() {

    const theExportMsgsBtn = document.querySelector('#export-messages');
    if ( theExportMsgsBtn ) {
        const removeAttribute = theExportMsgsBtn.removeAttribute;
        theExportMsgsBtn.removeAttribute = (key) => {
            if ( key == 'open' ) {
                window.location.reload(true);
            }
            removeAttribute.call(theExportMsgsBtn, key);
        };
    }

});

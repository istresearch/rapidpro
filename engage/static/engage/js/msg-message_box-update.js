/* functions if able to update msgs */

function onDeleteClicked(){
    var deleteConfirmation = document.querySelector("#delete-confirmation");
    deleteConfirmation.classList.remove("hide");
    deleteConfirmation.open = true;

    deleteConfirmation.addEventListener("temba-button-clicked", function(event){
        if (!event.detail.button.secondary) {
            runActionOnObjectRows("delete");
        }
        deleteConfirmation.open = false;
    });
  }

function handleCreateLabelModalLoaded(event) {
    window.lastChecked = getCheckedIds();
    var body = event.detail.body;
    body.querySelector("#id_messages").value = window.lastChecked.join();
}

function handleCreateLabelModalSubmitted(event) {
    refresh(function() { recheckIds(); }, true);
}

function handleSendMessageClicked() {
    let sendModal = document.querySelector("#send-message-modal");
    let msgIds = getCheckedIds();
    if ( msgIds.length > 0 ) {
        sendModal.setAttribute("endpoint", theSendMsgEndpoint + '?m=' + msgIds);
    } else {
        sendModal.setAttribute("endpoint", theSendMsgEndpoint);
    }
}

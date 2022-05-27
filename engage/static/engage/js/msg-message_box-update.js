/* functions if able to update msgs */

function handleCreateLabelModalLoaded(event) {
    let lastChecked = getCheckedIds();
    let body = event.detail.body;
    body.querySelector("#id_messages").value = lastChecked.join();
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

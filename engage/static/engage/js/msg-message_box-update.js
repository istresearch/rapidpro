/* functions if able to update msgs */

function handleCreateLabelModalLoaded(event) {
    lastChecked = getCheckedIds();
    var body = event.detail.body;
    body.querySelector("#id_messages").value = lastChecked.join();
}

function handleCreateLabelModalSubmitted(event) {
    refresh(function() { recheckIds(); }, true);
}

function handleSendMessageClicked() {
    var sendEndpoint = "{% url 'msgs.broadcast_send' %}";
    var sendModal = document.querySelector("#send-message-modal");
    var msgIds = getCheckedIds();
    if (msgIds.length > 0) {
        sendModal.setAttribute("endpoint", sendEndpoint + '?m=' + msgIds);
    } else {
        sendModal.setAttribute("endpoint", sendEndpoint);
    }
}

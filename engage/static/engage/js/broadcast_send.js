$(document).ready(function() {
    let rootSelectorName = "#send-msg";
    if ( document.querySelector("#send-message") ) {
        rootSelectorName = "#send-message";
    }
    else if ( document.querySelector("#send-message-modal") ) {
        rootSelectorName = "#send-message-modal";
    }
    else if ( $(document.querySelector("temba-modax")
        .shadowRoot.querySelector("temba-dialog")
        .shadowRoot.querySelector(".dialog-footer")
        .querySelector("temba-button[primary]"))[0] !== undefined )
    {
        rootSelectorName = "temba-modax";
    }

    let selector;
    try {
        selector = $(document.querySelector(rootSelectorName)
            .shadowRoot.querySelector("temba-dialog")
            .shadowRoot.querySelector(".dialog-footer")
            .querySelector("temba-button[primary]")
            .shadowRoot.querySelector("div")
        );
    } catch (e) {
        selector = null;
    }
    if ( selector && !selector.hasClass("confirm-click-handler") ) {
        let bIsAskingUser = false; //code might take a brief moment, prevent mutli-click-dialogs
        $(selector).addClass("confirm-click-handler").on("click", function (e) {
            let bUserChoseOK = false;
            if ( !bIsAskingUser ) {
                bIsAskingUser = true;

                let theText = $(document.querySelector(rootSelectorName)
                        .shadowRoot.querySelector("temba-dialog")
                        .querySelector(".modax-body")
                        .querySelector(".field_text")
                        .querySelector("temba-completion")
                        .querySelector("input")
                )[0].value;

                let theRecipients = [];
                $(document.querySelector(rootSelectorName)
                        .shadowRoot.querySelector("temba-dialog")
                        .querySelector(".modax-body")
                        .querySelector("div.controls")
                        .querySelectorAll("input")
                ).each(function () {
                    theRecipients.push(JSON.parse(this.value)["name"]);
                });

                bUserChoseOK = confirm(`Are you sure you want to send the message:\n${theText}\n\nto ${theRecipients.join(', ')}?`);
                bIsAskingUser = false;
            }
            if ( !bUserChoseOK ) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
});

$(document).ready(function() {
    let rootSelectorName = "#send-message";
    if ( $(document.querySelector("#send-message-modal") ) !== undefined ) {
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
    if ( selector ) {
        let bIsAskingUser = false; //code might take a brief moment, prevent mutli-click-dialogs
        $(selector).on("click", function (e) {
            let bUserChoseOK = undefined;
            if ( !bIsAskingUser && bUserChoseOK === undefined ) {
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

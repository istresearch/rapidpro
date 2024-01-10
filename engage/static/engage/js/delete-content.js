function handleDeleteSelectedContent(elemSelector = '#delete-confirmation'){
    const eDeleteConfirmation = document.querySelector(elemSelector);
    eDeleteConfirmation.classList.remove("hide");
    eDeleteConfirmation.open = true;

    eDeleteConfirmation.addEventListener("temba-button-clicked", (e) => {
      if ( !e.detail.button.secondary ) {
        runActionOnObjectRows("delete");
      }
      eDeleteConfirmation.open = false;
    });
}

function handleDeleteAllContent(elemSelector = '#delete-all-confirmation') {
    const eDeleteAllConfirmation = document.querySelector(elemSelector);
    eDeleteAllConfirmation.classList.remove("hide");
    eDeleteAllConfirmation.open = true;

    eDeleteAllConfirmation.addEventListener("temba-button-clicked", (e) => {
      if ( e.detail.button.attributes.destructive ) {
        jQuery.ajaxSettings.traditional = true;
        fetchPJAXContent(document.location.href, '#pjax', {
            postData: { action: "delete", all: 'true', pjax: 'true' },
            forceReload: true,
        });
      }
      eDeleteAllConfirmation.classList.add("hide");
      eDeleteAllConfirmation.open = false;
    });
}

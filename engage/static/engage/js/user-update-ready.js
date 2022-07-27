$(document).ready(function() {

    var menuitemDelete = document.querySelector("#action-delete-user");
    var dlgDelete = document.querySelector("#delete-confirmation");
    if ( menuitemDelete && dlgDelete ) {
        menuitemDelete.addEventListener("click", function(e) {
            dlgDelete.classList.remove("hide");
            dlgDelete.open = true;
        });

        dlgDelete.addEventListener("temba-button-clicked", function(e) {
            if ( !e.detail.button.secondary ) {
                doDeleteUser(menuitemDelete.getAttribute('data-submit-href'));
            }
            dlgDelete.open = false;
        });
    }

    var doDeleteUser = function( aUrl ) {
        $.ajax({ type: "POST", url: aUrl,
            success: function( data, textStatus, xhr ) {
                var gotoUrl = menuitemDelete.getAttribute('data-goto-href');
                if ( gotoUrl ) {
                    window.location.href = gotoUrl;
                } else {
                    var dlg = document.querySelector("#delete-success");
                    dlg.classList.remove("hide");
                    dlg.open = true;
                }
            },
            error: function( req, status, error ) {
                var dlg = document.querySelector("#delete-fail");
                dlg.querySelector('.fail-msg').innerHTML = req.status + " " + error;
                dlg.classList.remove("hide");
                dlg.open = true;
            }
        });
    };

});

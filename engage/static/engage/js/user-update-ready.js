$(document).ready(function() {

    var menuitemDelete = document.querySelector("#user-delete");
    var dlgDelete = document.querySelector("#delete-confirmation");
    if ( menuitemDelete && dlgDelete ) {
        menuitemDelete.addEventListener("click", function(e) {
            dlgDelete.classList.remove("hide");
            dlgDelete.open = true;
        });

        dlgDelete.addEventListener("temba-button-clicked", function(e) {
            if ( !e.detail.button.secondary ) {
                doDeleteUser(dlgDelete.getAttribute('href'));
            }
            dlgDelete.open = false;
        });
    }

    var doDeleteUser = function( aUrl ) {
        $.ajax({ type: "GET", url: aUrl,
            success: function( data, textStatus, xhr ) {
                var gotoUrl = menuitemDelete.getAttribute('goto_href');
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

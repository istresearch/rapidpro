$(document).ready(function() {
    if (navigator.appVersion.indexOf("Win")!=-1) {
        $("html").addClass("windows");
    }

    $(".btn").tooltip();

    var theOrgListBtn = $('#btn-org-list');
    if ( theOrgListBtn ) {
        theOrgListBtn.on('click', function(evt) {
            evt.stopPropagation();
            var header = $('.org-header');
            if (header.hasClass('expanded')) {
                header.removeClass('expanded');
            } else {
                header.addClass('expanded');
            }
        });
    }

    var theOrgPicker = $('#org-picker');
    if ( theOrgPicker ) {
        function formatOption (aOpt) {
            if (!aOpt.id) {
                return aOpt.text;
            }
            var theOpt = $(
                '<span class="' + $(aOpt.element).attr('class') + '">' + aOpt.text + '</span>'
            );
            return theOpt;
        };
        theOrgPicker.select2({
            dropdownParent: $('#org-area'),
            width: 'fit-content',
            theme: 'org-picker',
            templateResult: formatOption,
        });
        theOrgPicker.on('select2:select', function(e) {
            var theOrgPK = e.params.data.id;
            var theUrl = org_chosen_url_format.sprintf(theOrgPK);
            posterize(theUrl);
        });
        //$('#select2-selection__arrow').addClass('icon-menu-2');
    }

    var theOrgHomeBtn = $('#btn-org-home');
    if ( !theOrgHomeBtn ) theOrgHomeBtn = $('#org-name');
    if ( theOrgHomeBtn ) {
        theOrgHomeBtn.on('click', function(evt) {
            var theOrgPK = theOrgPicker ? theOrgPicker.find(':selected').value : '0';
            var theUrl = org_home_url_format.sprintf(theOrgPK);
            evt.stopPropagation();
            if (evt.ctrlKey || evt.metaKey){
                window.open(theUrl,'_blank')
            } else {
                window.location = theUrl;
            }
        });
    }

    var theMoreMenuEl = $('#menu .more');
    theMoreMenuEl.hoverIntent({
        over:function() {
            // $('.submenu').hide();
            $(this).find('.submenu-container').slideDown(100);
            $(this).parents("#menu").addClass('expanded');
            // $(this).find('.submenu').show();
        },
        out:function() {
            $(this).find('.submenu-container').slideUp(250);
            $(this).parents("#menu").removeClass('expanded');
            //$(this).find('.submenu').hide();
        },
        timeout:300
    });
    // friendlier UX if we remove ... HTML link clickability (it is "" anyway and does nothing)
    var theMoreMenuLinkEl = $('a', theMoreMenuEl);
    theMoreMenuLinkEl.removeAttr('href');

    $(".posterize").click(function(event){

        var ele = event.target;
        while (ele && !ele.classList.contains("posterize")) {
            ele = ele.parentElement;
        }

        event.preventDefault();
        event.stopPropagation();
        handlePosterize(ele);
    });

});

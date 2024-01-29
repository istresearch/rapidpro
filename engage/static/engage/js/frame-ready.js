window.app_spin_count = 0;
$(document).ready(function() {
    if (navigator.appVersion.indexOf("Win")!==-1) {
        $("html").addClass("windows");
    }

    $(".btn").tooltip();

    let theOrgListBtn = $('#btn-org-list');
    if ( theOrgListBtn ) {
        theOrgListBtn.on('click', function(evt) {
            evt.stopPropagation();
            const header = $('.org-header');
            if (header.hasClass('expanded')) {
                header.removeClass('expanded');
            } else {
                header.addClass('expanded');
            }
        });
    }

    const theBusySpinner = $('#busy-spinner');
    function showSpinner() {
        if ( window.app_spin_count++ === 0 ) {
            theBusySpinner.removeClass('hidden');
        }
    }
    function hideSpinner() {
        if ( window.app_spin_count-- === 1 ) {
            window.app_spin_count = 0;
            theBusySpinner.addClass('hidden');
        }
    }
    for (let ls = document.links, numLinks = ls.length, i=0; i<numLinks; i++) {
        ls[i].onclick= showSpinner;
    }
    //if using the Back button to return to a page where the spinner was shown before navigating away, handle it
    window.addEventListener('pageshow', function (e) {
        //typescript would need: (performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming).type
        if ( e.persisted || performance.getEntriesByType("navigation")[0].type === 'back_forward' ) {
            hideSpinner();
        }
    });

    let theOrgHomeBtn = $('#btn-org-home');
    const theOrgPicker = $('#org-picker');
    if ( theOrgPicker ) {
        function formatOption (aOpt) {
            if ( !aOpt.id ) {
                return aOpt.text;
            }
            let theOptClasses = $(aOpt.element).attr('class');
            let theOpt = $(
                '<span class="'+theOptClasses+'">' + aOpt.text + '</span><span class="state-icon '+theOptClasses+'"></span>'
            );
            return theOpt;
        }
        theOrgPicker.select2({
            dropdownParent: $('#org-area'),
            width: 'fit-content',
            theme: 'org-picker',
            templateResult: formatOption,
        });
        if ( theOrgHomeBtn ) {
            theOrgPicker.on('select2:select', function(e) {
                let theOrgPK = e.params.data.id;
                let theUrl = org_home_url_format.sprintf(theOrgPK);
                theOrgHomeBtn.prop('href', theUrl);
                theUrl = org_chosen_url_format.sprintf(theOrgPK);
                posterize(theUrl);
            });
        }
    }

    if ( !theOrgHomeBtn ) {
        theOrgHomeBtn = $('#org-name');
        theOrgHomeBtn.on('click', function(evt) {
            let theOrgPK = theOrgPicker ? theOrgPicker.find(':selected').val() : '0';
            let theUrl = org_home_url_format.sprintf(theOrgPK);
            evt.stopPropagation();
            if (evt.ctrlKey || evt.metaKey){
                window.open(theUrl,'_blank')
            } else {
                theBusySpinner.removeClass('hidden');
                window.location = theUrl;
            }
        });
    }

    let theMoreMenuEl = $('#menu .more');
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
    let theMoreMenuLinkEl = $('a.icon-menu-4', theMoreMenuEl);
    theMoreMenuLinkEl.removeAttr('href');

    $(".posterize").click(function(event){

        let ele = event.target;
        while (ele && !ele.classList.contains("posterize")) {
            ele = ele.parentElement;
        }

        event.preventDefault();
        event.stopPropagation();
        handlePosterize(ele);
    });

    if (window.scheduleRefresh) {
      scheduleRefresh();
    }
});

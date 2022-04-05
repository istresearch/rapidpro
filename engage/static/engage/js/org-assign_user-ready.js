$(document).ready(function() {

    //var theOrgPicker = $('#assign-user-org-picker');
    var theOrgPicker = $('#id_organization');
    if ( theOrgPicker ) {
        function formatOption (aOpt) {
            if (!aOpt.id) {
                return aOpt.text;
            }
            var theOptClasses = $(aOpt.element).attr('class');
            var theOpt = $(
                '<span class="'+theOptClasses+'">' + aOpt.text + '</span><span class="status-icon '+theOptClasses+'"></span>'
            );
            return theOpt;
        };
        theOrgPicker.select2({
            //dropdownParent: $('#org-area'),
            width: 'fit-content',
            //theme: 'org-picker',
            templateResult: formatOption,
        });
        /*
        theOrgPicker.on('select2:select', function(e) {
            var theOrgPK = e.params.data.id;
            var theUrl = org_chosen_url_format.sprintf(theOrgPK);
            posterize(theUrl);
        });
        */
    }

});

$(document).ready(function() {

    var theOrgPicker = $('#id_organization');
    if ( theOrgPicker ) {
        function formatOption (aOpt) {
            if (!aOpt.id) {
                return aOpt.text;
            }
            var theOptClasses = $(aOpt.element).attr('class');
            var theOpt = $(
                '<span class="'+theOptClasses+'">' + aOpt.text + '</span><span class="state-icon '+theOptClasses+'"></span>'
            );
            return theOpt;
        };
        theOrgPicker.select2({
            width: 'fit-content',
            templateResult: formatOption,
        });
    }

});


function initPanZoom( elDesktop ) {
    const theEl = elDesktop;
    const bZoomEnabled = false;
    const $panzoom = Panzoom(theEl, {
        minScale: 0.5,
        maxScale: 2,
        step: 0.05,
        disableZoom: !bZoomEnabled, //until floweditor supports grabbing the scale from this obj
        disablePan: true,
        cursor: "",
        canvas: true,
        exclude: [document.getElementById('rp-flow-editor')],
        excludeClass: ['jtk-draggable', 'pop_wrapper'],
    });

    $(theEl).parent().on('mousewheel.focal', (e) => {
        //e.preventDefault();
        let deltaY = e.deltaY || e.originalEvent.wheelDeltaY || (-e.originalEvent.deltaY);
        let deltaX = e.deltaX || e.originalEvent.wheelDeltaX || (-e.originalEvent.deltaX);
        if ( !(e.ctrlKey || e.originalEvent.ctrlKey) && bZoomEnabled && deltaY ) {
            let bZoomOut = deltaY ? deltaY < 0 : e.originalEvent.deltaY > 0;
            let zoomOpts = {
               animate: true,
               exponential: false,
            };
            if ( bZoomOut ) {
                $panzoom.zoomOut(zoomOpts);
            } else {
                $panzoom.zoomIn(zoomOpts);
            }
        } else {
            $panzoom.setOptions({
                disablePan: false,
            });
            $panzoom.pan( deltaX / 2, deltaY / 2, {
                animate: true,
                relative: true,
            });
            $panzoom.setOptions({
                disablePan: true,
            });
        }
    });
    return $panzoom;
}
let flowEditorPanzoom;
window.addEventListener("DOMContentLoaded", function() {
    const elDesktop = document.getElementById('rp-flow-editor');
    flowEditorPanzoom = initPanZoom(elDesktop);

    const menuitemReCenter = document.querySelector("#action-recenter");
    if ( menuitemReCenter ) {
        menuitemReCenter.addEventListener("click", (e) => {
            flowEditorPanzoom.reset();;
        });
    }

});

function initPanzoom() {
    // called inside the haml file where used when flow editor finishes loading (important!)
    let elDesktop;
    let flowEditorPanzoom;
    const configPanZoom = {
        minScale: 0.05,
        maxScale: 1.6,
        step: 0.05,
        disableZoom: false,
        disablePan: false,
        cursor: "",
    };

    function configurePanZoom(elDesktop) {
        const theEl = elDesktop;
        let config = Object.assign(configPanZoom, {
            canvas: true,
            exclude: Array.from(document.querySelectorAll('div[class^=CanvasDraggable]')),
        });
        let zoomOpts = {
            animate: true,
            exponential: false,
        };
        let panOpts = {
            animate: true,
            relative: true,
        };
        const $panzoom = Panzoom(theEl, config);

        $(theEl).parent().on('mousewheel.focal', (e) => {
            let deltaY = e.deltaY || e.originalEvent.wheelDeltaY || (-e.originalEvent.deltaY);
            let deltaX = e.deltaX || e.originalEvent.wheelDeltaX || (-e.originalEvent.deltaX);
            if ( !config.disableZoom && (e.ctrlKey || e.originalEvent.ctrlKey) && deltaY ) {
                e.preventDefault();
                let bZoomOut = deltaY ? deltaY < 0 : e.originalEvent.deltaY > 0;
                if ( bZoomOut ) {
                    $panzoom.zoomOut(zoomOpts);
                } else {
                    $panzoom.zoomIn(zoomOpts);
                }
            } else if ( !config.disablePan && deltaX ) {
                $panzoom.pan(deltaX/2, deltaY/2, panOpts);
            }
        });

        return $panzoom;
    }

    elDesktop = document.getElementById('canvas-container');
    flowEditorPanzoom = configurePanZoom(elDesktop);

    const menuitemReCenter = document.querySelector("#action-recenter");
    if ( menuitemReCenter && flowEditorPanzoom ) {
        menuitemReCenter.addEventListener("click", (e) => {
            flowEditorPanzoom.reset();
        });
    }
}

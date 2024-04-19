function initLeafletMap(geoObj) {
    let shape = null;
    let maxZoom = 15;
    const leafletData = window.leafletData;
    const L = window.L;

    let geoType = geoObj.type || 'point';

    leafletData.getMap().then((map) => {
        if (geoType === 'circle') {
            shape = new L.Circle(
                [geoObj.bounds._center.lat, geoObj.bounds._center.lng],
                {radius: geoObj.radius, color: 'red'}
            ).addTo(map);
        } else if ( geoType === 'polygon' ) {
            shape = new L.Polygon(
                [[geoObj.bounds._northEast.lat, geoObj.bounds._northEast.lng],
                 [geoObj.bounds._northEast.lat, geoObj.bounds._southWest.lng],
                 [geoObj.bounds._southWest.lat, geoObj.bounds._southWest.lng],
                 [geoObj.bounds._southWest.lat, geoObj.bounds._northEast.lng]],
                {color: 'red'}
            ).addTo(map);
        } else if (geoType === 'point') {
            maxZoom = 13;
            shape = new L.Circle(
                [geoObj.bounds._center.lat, geoObj.bounds._center.lng],
                {radius: 10, fill: true, fillOpacity: 1, color: 'red'}
            ).addTo(map);
        }

        map.fitBounds(shape.getBounds(), {maxZoom: maxZoom});
    });
}

function refreshLeaflet(leafletMap) {
    if ( leafletMap ) {
        leafletMap.invalidateSize();
        leafletMap._resetView(leafletMap.getCenter(), leafletMap.getZoom(), true);
    }
}

function shortenGeoValue(input, geoType) {
    if ( !input ) {
        return null;
    }
    const L = window.L;

    let values = input.replace(/[ ,]+/g, ",").split(","),
        output = [];

    for (let i = 0, len = values.length; i < len; i++) {
        let val = parseFloat(values[i].split('=').pop());

        if (geoType === 'circle' && i === 2) {
            val = val / 1000;
        }

        output.push(
            L.Util.formatNum(val, 6)
        );
    }

    return output.join(',');
}

function getGeoValue(geoObj) {
    return shortenGeoValue(geoObj.value, geoObj.type);
}

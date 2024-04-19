function initLeafletMap(geoObj, config=null) {
    const defaultConfig = {
        leaflet: {
            id: 'road_map',
            url: 'https://tiles.maps.elastic.co/v2/default/{z}/{x}/{y}.png',
            urlparams: {
                elastic_tile_service_tos: 'agree',
                my_app_name: leaflet_app_name,
                license: leaflet_token,
            },
            //tileLayer: LEAFLET.url + $rootScope.userInfo.maps_lickey,
            minZoom: 0,
            maxZoom: 18,
            attribution: '&copy; [OpenStreetMap](http://www.openstreetmap.org/copyright) contributors | [Elastic Maps Service](https://www.elastic.co/elasticmapsservice)',
        },
        mapCenter: { // for geo coordinates
            lat: 51,
            lng: 0,
            zoom: 4
        },
        areaSelectOptions: {
            width: 100,
            height: 100,
            geoType: 'polygon'
        },
    };
    config = {...config, ...defaultConfig};

    let shape = null;
    let maxZoom = 15;
    const leafletData = window.leafletData;
    const L = window.L;

    let geoType = geoObj.type || 'point';

    config.areaSelectOptions.geoType = geoType;
    let areaSelect = new L.AreaSelect(config.areaSelectOptions);

    leafletData.getMap().then((map) => {
        /*
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
         */
        areaSelect.addTo(map);
        /*
        areaSelect.on("change", () => {
            let bounds = this.getBounds();
            let center = this.getCenter();
            geoObj.valueChanged = false;
            geoObj.value = geoType === 'circle' ? GeoService.createStringForCircle(center, bounds) :
                           geoType === 'polygon' ? GeoService.createStringForPolygon(bounds) :
                           geoType === 'point' ? GeoService.createStringForPoint(center) : null;
        });
        if (geoObj.value) {
            areaSelect.setBounds(GeoService.getCoordsFromString(scope.newRule.type, scope.newRule.value));
        }
        */

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

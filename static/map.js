"use strict";

var map;
var mapView;
var boundary;
var backBoundary;
var fence;
var assetMarker = new google.maps.Marker();
var firstIcon = 'http://maps.google.com/mapfiles/ms/micons/blue.png';
var firstMarker = new google.maps.Marker({
    icon: firstIcon,
    title: "Fence",
    nowrap: false
});
var setFenceCB = null;


function initialize() {
    var Bangalore = new google.maps.LatLng(12.972107, 77.589912);
    var mapOptions = {
        zoom: 11,
        center: Bangalore,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

    google.maps.event.addListener(map, 'click', addPoint);

    google.maps.event.addListener(assetMarker, 'click', function() {
        if (fence) {
            var path = fence.getPath();
            changeMapView(path, assetMarker.getPosition(), true);

        } else {
            map.panTo(assetMarker.getPosition())
            map.setZoom(10);
        }
    });

    google.maps.event.addListener(firstMarker, 'click', function() {
        var path = fence.getPath();
        changeMapView(path, path[0], true)
    });

    boundary = new google.maps.Polyline({
        strokeColor: "#FF0000",
        strokeOpacity: 0.8,
        strokeWeight: 3
    });

    backBoundary = new google.maps.Polyline({
        strokeColor: "#FFAAAA",
        strokeOpacity: 0.5,
        strokeWeight: 3
    });

    fence = new google.maps.Polygon({
        strokeColor: "#FF0000",
        strokeOpacity: 0.0,
        strokeWeight: 0,
        fillColor: "#00FF00",
        fillOpacity: 0.25,
        clickable: false
    });

    boundary.setMap(map);
    backBoundary.setMap(map);
    fence.setMap(map);
}

// map a new point to the boundary polyline (happens on click).

function addPoint(event) {
    fence.setOptions({
        fillColor: "#0000FF"
    });
    var path = boundary.getPath();
    path.push(event.latLng);

    var back = backBoundary.getPath();
    if (path.getLength() == 1) {
        firstMarker.setOptions({
            position: event.latLng,
            title: "First Point",
            map: map
        });
    }
    if (path.getLength() == 1 || path.getLength() == 2) {
        back.push(event.latLng);
    } else {
        back.pop();
        back.push(event.latLng);
    }
}

// Removes the polyline representing the new fence

function reset() {
    firstMarker.setMap(null);
    clearBoundary();
    fence.setPath([]);
    if (setFenceCB != null) {
        setFenceCB([]);
    }
}


function clearBoundary() {
    boundary.setPath([]);
    backBoundary.setPath([]);
    firstMarker.setMap(null);
}


function setAssetLocation(assetInfo) {
    assetInfo = assetInfo.payload;
    if (assetInfo == null) {
        assetMarker.setMap(null);
    } else {
        var assetLocation = new google.maps.LatLng(assetInfo.latitude,
                                                   assetInfo.longitude);
        assetMarker.setOptions({
            map: map,
            position: assetLocation,
            title: "Asset",
            nowrap: false
        });

        if (mapView != null) {
            mapView.extend(assetLocation);
        }
    }
}


function changeMapView(path, assetLocation, moveMap) {
    if (assetMarker.getMap() == null) assetLocation = null;

    if (path.getArray().length > 2) {
        mapView = null;
        mapView = new google.maps.LatLngBounds(assetLocation || path[0]);

        var coord;
        for (coord in path.getArray()) {
            mapView.extend(path.getArray()[coord]);
        }

        if (moveMap) {
            map.setZoom(3);
            map.fitBounds(mapView);
        }

    } else if (assetLocation) {
        map.panTo(assetLocation);
        map.setZoom(10);
    } else {
        alert("This asset does not have a last location or a geofence.");
    }
}

// Sets the polyline to be the new fence

function setFenceFromBoundary() {

    if(boundary.getPath().getArray().length <= 2) {
        alert("Geofences must have at least three points!");
        return;
    }

    firstMarker.setMap(null);
    mapView = null;

    fence.setOptions({
        fillColor: "#00FF00"
    });
    fence.setPath(boundary.getPath());
    clearBoundary();
    if (setFenceCB != null) {
        var latlng = fence.getPath().getArray();
        var fenceArray = [];
        var coord;
        for (coord in latlng) {
            fenceArray[coord] = [latlng[coord].lat(), latlng[coord].lng()];
        }
        setFenceCB(fenceArray);
    }

    changeMapView(fence.getPath(), assetMarker.getPosition(), false);

    if (fence) {
        firstMarker.setOptions({
            position: fence.getPath().getArray()[0],
            map: map
        });
    }

}


function setFenceFromPoints(points) {
    firstMarker.setMap(null);
    fence.setOptions({
        fillColor: "#00FF00"
    });
    fence.setPath([]);
    clearBoundary();
    var path = fence.getPath();
    var pt;
    for (pt in points) {
        var coord = new google.maps.LatLng(points[pt][0], points[pt][1], true);
        path.push(coord);
    }

    changeMapView(path, assetMarker.getPosition(), true);

    if (fence) {
        firstMarker.setOptions({
            position: fence.getPath().getArray()[0],
            map: map
        });
    }
}


google.maps.event.addDomListener(window, 'load', initialize);

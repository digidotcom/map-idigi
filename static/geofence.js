"use strict";

var updateAssets = function(data) {
    if (data.logged_in == false) {
        location.reload(true)
    }
    //var keys = Object.keys(data.payload);
    var assets = $('#assets');
    var table2 = $('<table>').addClass('atable')
    var i = 0;
    var payload = data.payload;
    for (var a in payload) {
        var asset = $('<tr>')
        if (!(i % 2)) {
            asset.addClass('odd');
        }
        i++;

        asset
            .append($('<td>')
                    .append($('<input>')
                            .attr('type', 'radio')
                            .attr('name', 'asset')
                            .attr('value', a)
                            .attr('onclick', 'clearAssetTimeout();updateGeofence(' + a + ');')))
            .append($('<td>')
                    .append(a))
            .append($('<td>')
                    .append(payload[a].name))
            .append($('<td>')
                    .append(payload[a].description))
        asset.appendTo(table2);
    };
    table2.appendTo(assets);

};


var updateGeofence = function(asset) {
    //This function redraws the fence on the map
    updateAssetLive(asset);
    jQuery.ajax({
        url: '/geofence/asset/' + asset + '/geofence',
        dataType: 'json',
        success: function(data) {
            // data is an array of arrays
            // with form (lat, long)
            if (data.payload != null) {
                setFenceFromPoints(data.payload);
            } else {
                setFenceFromPoints([]);
            }
        },
        async: false,
        cache: false,
        statusCode: window.mobile_assets.statusCodes
    });

    setFenceCB = function(fence) {
        sendGeofence(asset, fence, "inclusive");
    };
};

var assetTimeout = null;

var updateAssetLive = function(asset) {
    jQuery.ajax({
        url: '/geofence/asset/' + asset + '/location',
        dataType: 'json',
        success: setAssetLocation,
        async: false,
        cache: false,
        statusCode: window.mobile_assets.statusCodes
    });

    assetTimeout = setTimeout(function() {
        updateAssetLive(asset);
    }, 30000);
};


var clearAssetTimeout = function() {
    if (assetTimeout) {
        clearInterval(assetTimeout);
        assetTimeout = null;
    }
};

var sendGeofence = function(asset, fence, id) {
    $.ajax({
        type: 'PUT',
        dataType: 'json',
        url: '/geofence/asset/' + asset + '/geofence',
        data: 'fence=' + encodeURIComponent(JSON.stringify(fence))+'&id='+id,
        contentType: 'application/x-www-form-urlencoded',
        statusCode: window.mobile_assets.statusCodes,
        success: function(data) {
            alert(data.code + ": " + data.message);
        }
    });
};


jQuery.ajax({
    url: '/geofence/asset',
    dataType: 'json',
    success: updateAssets,
    async: false,
    cache: false,
    statusCode: window.mobile_assets.statusCodes
});


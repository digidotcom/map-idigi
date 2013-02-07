(function() {
    assetId = null

    function fake_refresh() {
        return "Not Available"
    }

    var getInfo = function (data, assetId) {
        //Only pulls the first object out of the data array
        var infoUl = $('<ul>');
        infoUl.attr('id', 'info' + assetId)
        records = data[0];
        for (var record in records) {
            infoUl.append($('<li>')
                          .html('<strong>' + record + ':</strong> ' +
                                (records[record] == null ? fake_refresh() : records[record])));
        }
        return infoUl;
    };

    var refresh = function(e) {
        assetId = $(this).data('id')
        $.ajax({
            success: function(data) {
                data = data.payload[assetId];
                assetInfo = $('#info' + assetId);
                assetInfo.empty();
                ul = getInfo(data, assetId)
                assetInfo.replaceWith(ul)
            },
            type: 'GET',
            url: '/obd/asset/' + assetId + '/obd/',
            async: false,
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });
    };


    var updateOBD = function(data) {
        $('#obdContainer').empty()
        for (var asset in data) {

            var d = data[asset];

            var obdBox = $('<div>')
                .attr('id', "asset" + asset)
                .attr('class', 'box');

            var link = $('<a></a>')
                .attr('href', '')
                .attr('class', 'collapse')
                .append($('<span></span>')
                        .addClass('idnumber')
                        .append(asset))
                .append($('<span></span>')
                        .addClass('name')
                        .append(d['deviceId']))
                .append($('<span></span>')
                        .addClass('righttext')
                        .text((d['Date Created'] === null ? '<Date>' : d[0]['Date Created'])));

            var actions = $('<ul>')
                .addClass('actions')
                .append($('<li>').html('<a class="refresh" data-id="' + asset + '">Refresh</a>'))

            var info = getInfo(d, asset);

            $('#obdContainer')
                .append(obdBox
                        .append(link)
                        .append($('<div>')
                                .append(actions)
                                .append(info)));
        }
    };


    $.ajax({
        success: function(data) {
            data = data.payload;
            for (var asset in data) {
                $('.h4').append(' For Asset ' + asset);
                assetId = asset;
            }
            updateOBD(data);
        },
        type: 'GET',
        url: location.toString() + 'obd/',
        async: false,
        cache: false,
        dataType: 'json',
        statusCode: window.mobile_assets.statusCodes
    });

    $('body').on('click', '.collapse', window.mobile_assets.collapse);
    $('body').on('click', '.refresh', refresh);

    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
        $('#obdContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }
})()

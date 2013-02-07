(function() {
    var getAssetAlerts = function(data) {
        for (var i = 0; i < data.length; i++) {
            $('#alertsContainer').empty()
            var alert_ = data[i];

            var box = $('<div>')
                .addClass('box')

            var link = $('<a></a>')
                .attr('href', '')
                .attr('class', 'collapse')
                .append($('<span></span>')
                        .addClass('idnumber')
                        .append(alert_['type']))
                .append($('<span></span>')
                        .append(alert_['desc']))
            //.append($('<span></span>')
            //      .addClass('righttext')
            //    .append(alert_['desc'] == null ? 'No description' : alert_['desc']));

            if (alert_['trouble']) {
                link.addClass('trouble');
            }

            var info = $('<ul>')
                .append($('<li>').html('<strong>Time: </strong>' + alert_['time']))
                .append($('<li>').html('<strong>Alert: </strong>' + alert_['Alert']))
                .append($('<li>').html('<strong>Distance: </strong>' + alert_['distance']))
                .append($('<li>').html('<strong>Location:\r\n\t</strong>'
                                       + '(' + alert_['latitude'] + ', ' + alert_['longitude'] + ')'));

            $('#alertContainer')
                .append(box
                        .append(link)
                        .append($('<div>')
                                .append(info)));
        }
    };

    $.ajax({
        success: function(data) {
            data = data.payload;
            for (var asset in data) { //There should only be one asset in the response
                $('.h4').append(' For Asset ' + asset);
                getAssetAlerts(data[asset]);
            }
        },
        type: 'GET',
        url: location.toString() + 'alert/',
        async: false,
        cache: false,
        dataType: 'json',
        statusCode: window.mobile_assets.statusCodes
    });

    $('body').on('click', '.collapse', window.mobile_assets.collapse);
    $('.collapse').click();
    
    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
    	$('#alertContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }
})()

"use strict";
(function() {
    var provisionDevice = function(e) {
        var data = $('#deviceForm').serializeArray()
        $.ajax({
            url: '/device/device/',
            type: 'PUT',
            dataType: 'json',
            data: data,
            success: function(data, textStatus, jqXHR) {
                alert(data.code + ": " + data.message);
                window.location = window.location;
            },
            statusCode: window.mobile_assets.statusCodes
        })
    }

    $.ajax({
        url:'device/mobile_operators/',
        type: 'GET',
        cache: false,
        dataType: 'json',
        success: function(data) {
            data = data['payload'];
            $('.operators').children().remove();

            for (var key in data) {
                $('.operators').append(
                    $('<option></option>')
                        .attr('value', key).text(data[key]));
            }
        },
        statusCode: window.mobile_assets.statusCodes
    });

    $.ajax({
        url: 'device/device_types/',
        type: 'GET',
        cache: false,
        dataType: 'json',
        success: function(data) {
            data = data['payload'];
            $('.devTypes').children().remove();

            for (var key in data) {
                $('.devTypes').append(
                    $('<option></option>')
                        .attr('value', key).text(data[key]));
            }
        },
        statusCode: window.mobile_assets.statusCodes
    });

    $('body').on('click', '.saveDevice', provisionDevice);

    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
    	$('#deviceContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }
})()


"use strict";
(function() {
    var saveConfig = function(e) {
        $.ajax({
            url: window.location.pathname,
            type: 'PUT',
            success: function(data) {
                alert(data.message.code + ': ' + data.message.message);
                window.location = "/asset/";
            },
            data: $('#configForm').serializeArray(),
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });

        e.preventDefault();
    }

    // HACK because apprently Waypoint is not yet implemented
    // TODO: remove this terrible HACK as soon as possible.
    $('h3:contains("Waypoint")').parent().remove() // Please FIXME

    var cancelConfig = function(e) {
        window.location = "/asset/";
    }

    $('body').on('click', '.saveConfig', saveConfig);
    $('body').on('click', '.cancelConfig', cancelConfig);
    
    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
    	$('#configForm > div:nth-child(odd)').addClass('ieCompatRow');
    }

})();


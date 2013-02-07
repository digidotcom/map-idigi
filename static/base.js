"use strict";
(function() {
    var statusCodes = {
        "cleanUp": function (code) {},
        401: function(jqXHR, textStatus, errorThrown) {
            alert('Invalid Credentials, Please log in again.');
            statusCodes.cleanUp(401);
            window.location = '/logout';
        },
        403: function(jqXHR, textStatus, errorThrown) {
            alert('403: ' + JSON.parse(jqXHR.responseText).message);
            statusCodes.cleanUp(403);
        },
        502: function(jqXHR, textStatus, errorThrown) {
            alert('502: ' + JSON.parse(jqXHR.responseText).message);
            statusCodes.cleanUp(502);
        },
        500: function(jqXHR, textStatus, errorThrown) {
            alert('500: ' + JSON.parse(jqXHR.responseText).message);
            statusCodes.cleanUp(500);
        }
    },

    collapse = function(e) {
        var height = $(this).data('height');
        var ele = $(this);
        var options = {
            'duration': 200
        };

        // Check to see if a height exists on the element
        // If the height exists, that means it has been shrunk so we want to unshrink it
        // If the height does not exist, store the height in the element and then shrink it
        if (height) {
            ele.parent().animate({
                'height': height
            }, options);
            $.removeData(this, 'height')
            ele.css('background-image', 'url(/static/images/arrow-down.png)');
        } else {
            ele.data('height', ele.parent().height());

            ele.parent().animate({
                'height': 28
            }, options);
            ele.css('background-image', 'url(/static/images/arrow.png)');
        }

        e.preventDefault();
    };

    var loadingDots = function(element) {
        var dots = setInterval(function() {
            element.append('.');
        }, 1000);
        return dots
    }

    var mobile_assets = {
        'statusCodes': statusCodes,
        'collapse': collapse,
        'loadingDots': loadingDots,
    };

    $('body').on('click', '.collapse', function() { this.blur(); } );

    window.mobile_assets = mobile_assets;
})();

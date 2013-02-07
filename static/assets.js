"use strict";

(function() {
    var setUp =  function() {
        var originalCleanUp = window.mobile_assets.statusCodes.cleanUp;
        function cleanUp(code) {
            if (code == 403) {
                $(".cancelAsset").click();
            }
            originalCleanUp(code);
        }
        window.mobile_assets.statusCodes.cleanUp = cleanUp;
    }
    setUp();


    var updateAssets = function(data) {
        var html = '';

        for (var i = 0, length = data['payload'].length; i < length; i++) {
            var d = data['payload'][i];
            var assetIdStr = 'asset' + d['assetId'];

            var assetBox = $('<div></div>')
                .attr('id', assetIdStr)
                .attr('class', 'box');

            var link = $('<a></a>')
                .attr('href', '')
                .attr('class', 'collapse')
                .append($('<span></span>')
                        .addClass('idnumber')
                        .append(d['assetId']))
                .append($('<span></span>')
                        .addClass('name')
                        .append(d['name']))
                .append($('<span></span>')
                        .addClass('righttext')
                        .append(d['Description'] == null ? 'No description' : d['Description']));

            var acts = $('<ul></ul>')
                .addClass('actions')
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('showEditAsset')
                                .attr('data-id', assetIdStr)
                                .attr('data-url', '/asset/asset/' + d['assetId'])
                                .append('Edit')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('showDeleteAsset')
                                .attr('data-id', assetIdStr)
                                .attr('data-url', '/asset/asset/' + d['assetId'])
                                .append('Delete')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .attr('href', '/alert/asset/' + d['assetId'] + '/')
                                .append('Alerts')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .attr('href', '/obd/asset/' + d['assetId'] + '/')
                                .append('OBD')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .attr('href', '/config/config/asset/' + d['assetId'] )
                                .append('Config')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('pollAsset')
                                .attr('data-id', assetIdStr)
                                .attr('data-url', '/asset/poll/' + d['assetId'])
                                .append('Poll')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('beginTrack')
                                .attr('data-url', '/asset/track/' + d['assetId'])
                                .append('Track')))
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('stopTrackAsset')
                                .attr('data-url', '/asset/stop_track/' + d['assetId'])
                                .append('Untrack')));

            var info1 = $('<ul></ul>')
                .append($('<li></li>').html('<strong>Name:</strong> <span class="assetname">' + d['Name'] + '</span>'))
                .append($('<li></li>').html('<strong>ID_Number:</strong> ' + d['ID_Number']))
                .append($('<li></li>').html('<strong>Device Serial</strong> ' + d['device_serial']))
                .append($('<li></li>').html('<strong>Last_Updated:</strong> ' + d['Last_Updated']))
                .append($('<li></li>').html('<strong>Description:</strong> <span class="assetdescription">' + d['Description'] + '</span>'))
                .append($('<li></li>').html('<strong>Status:</strong> <span class="assetstatus">' + d['status'] + '</span>'));

            var info2 = $('<ul></ul>')
                .append($('<li></li>').html('<strong>Org_ID:</strong> ' + d['Org_ID']))
                .append($('<li></li>').html('<strong>assetId:</strong> ' + d['assetId']));

            if (d['Last Location']['Updated'] == null) {
                info2.append($('<li></li>').html('<strong>Last Location:</strong>' + ' N/A'))
            } else {
                info2.append($('<ul></ul>')
                             .append($('<li></li>').html('<strong>Coordinates:</strong> '
                                                         + d['Last Location']['Coordinates'][0] + ', '
                                                         + d['Last Location']['Coordinates'][1]))
                             .append($('<li></li>').html('<strong>Near:</strong> ' + d['Last Location']['Near']))
                             .append($('<li></li>').html('<strong>Updated:</strong> ' + d['Last Location']['Updated'])))
            };


            $('#assetsContainer')
                .append(assetBox
                        .append(link)
                        .append($('<div></div>')
                                .append(acts)
                                .append(info1)
                                .append(info2)));


        }
    }

    $.ajax({
        success: updateAssets,
        url: '/asset/asset',
        async: false,
        cache: false,
        dataType: 'json',
        statusCode: window.mobile_assets.statusCodes
    })

    var showLightbox = function(box, assetTypeCB) {
        var lb = $(box),
        div = $(box + ' > div');

        lb.fadeIn('fast').css('top', $(window).scrollTop());

        // Center the lightbox in the window
        div.css({
            top: (lb.outerHeight() - div.outerHeight()) / 2,
            left: (lb.outerWidth() - div.outerWidth()) / 2
        });

        // Update the unused serials select on the page
        $.ajax({
            url: '/asset/device/unused_serial',
            success: function(data) {
                data = data['payload'];

                $('.unusedSerials').children().remove();

                for (var i = 0, len = data.length; i < len; i++) {
                    $('.unusedSerials').append(
                        $('<option></option>').attr('value', data[i]).text(data[i]));
                }
            },
            statusCode: window.mobile_assets.statusCodes,
            cache: false,
            dataType: 'json'
        })

        $.ajax({
            url: 'asset/asset_types/',
            type: 'GET',
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes,
            success: function(data) {
                data = data['payload'];
                $('.assetTypes').children().remove();

                for (var key in data) {
                    $('.assetTypes').append(
                    $('<option></option>')
                        .attr('value', key).text(data[key]));
                }
            }

        });
    }

    var hideLightbox = function(e) {
        // Fadeout all of the lightboxes
        $('.lightbox').fadeOut('fast');
    }

    var showAddAsset = function(e) {
        showLightbox('.addBox');

        e.preventDefault();
    }


    var saveAsset = function(e) {
        $.ajax({
            url: '/asset/asset',
            type: 'POST',
            success: function(data) {
                // Reload the page once we have a success
                alert(data.message.code + ': ' + data.message.message);
                window.location = window.location;
            },
            data: $('#assetForm').serializeArray(),
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });

        hideLightbox();
        e.preventDefault();
    }

    var modifyAsset = function(e) {
        $.ajax({
            success: function() {
                // Reload the page once we have a success
                window.location = window.location;
            },
            url: $(this).data('url'),
            type: 'PUT',
            data: $('#editForm').serializeArray(),
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });

        hideLightbox();
        e.preventDefault();
    }


    // Shows the lightbox and dynamically adds the values of
    // the span elements to the input boxes
    var showEditAsset = function(e) {
        var $this = $(this),
        asset = $('#' + $this.data('id'));

        showLightbox('.editBox');

        $('.modifyAsset').data('url', $(this).data('url'));

        $('#editForm input[type!=button]').each(function(i, e) {
            var $e = $(e),
            n = $e.attr('name');

            $e.val(asset.find('.asset' + n).text());
        });

        e.preventDefault();
    }

    var showDeleteAsset = function(e) {
        var result = confirm('Are you sure you want to delete this asset? Deleting is a permanent operation and information *will* be lost.');

        if (result) {
            $.ajax({
                success: function() {
                    // Reload the page once we have a success
                    window.location = window.location;
                },
                url: $(this).data('url'),
                type: 'DELETE',
                cache: false,
                dataType: 'json',
                statusCode: window.mobile_assets.statusCodes
            })
        }

        hideLightbox();
        e.preventDefault();
    }

    var pollStartStop = function(e) {
        $.ajax({
            success: function(data) {
                alert(data.payload.code + ': ' + data.payload.message);
            },
            data: null,
            url: $(this).data('url'),
            type: 'POST',
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });
    }

    // Bind the onclick events
    // By default, we want all of our divs to be collapsed
    $('.collapse').bind('click', window.mobile_assets.collapse).click();

    $('body').on('click', '.showAddAsset', showAddAsset);
    $('body').on('click', '.saveAsset', saveAsset);
    $('body').on('click', '.showDeleteAsset', showDeleteAsset);
    $('body').on('click', '.showEditAsset', showEditAsset);
    $('body').on('click', '.modifyAsset', modifyAsset);
    $('body').on('click', '.cancelAsset', hideLightbox);
    $('body').on('click', '.pollAsset', pollStartStop);
    $('body').on('click', '.beginTrack', pollStartStop);
    $('body').on('click', '.stopTrackAsset', pollStartStop);
    
    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
        $('#assetsContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }
})();

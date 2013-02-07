"use strict";

(function() {
    var setUp =  function() {
        var originalCleanUp = window.mobile_assets.statusCodes.cleanUp;
        function cleanUp(code) {
            if (code == 403) {
                $(".cancel").click();
            }
            originalCleanUp(code);
        }
        window.mobile_assets.statusCodes.cleanUp = cleanUp;
    }
    setUp();


    var updateOrgs = function(data) {
        var orgId = data.yourOrgId;
        var parentId = data.yourParentId;
        var orgs = data.orgInfo;
        for (var i = 0, length = orgs.length; i < length; i++) {
            var org = orgs[i];

            var orgBox = $('<div></div>')
                .attr('id', org.orgId)
                .attr('class', 'box');

            var link = $('<a></a>')
                .attr('href', '')
                .attr('class', 'collapse')
                .append($('<span>')
                        .addClass('idnumber')
                        .append(org.orgId))
                .append($('<span>')
                        .addClass('name'))
                .append($('<span>')
                        .append(org.name));

            var actions = $('<ul></ul>')
                .addClass('actions')
                .append($('<li></li>')
                        .append($('<a></a>')
                                .addClass('showEditOrg')
                                .attr('data-id', org.orgId)
                                .attr('data-url', '/org/org/' + org.orgId)
                                .append('Edit')));

            var info = $('<ul></ul>')
                .append($('<li></li>').html('<strong>ID_Number: </strong>' + org.orgId))
                .append($('<li></li>').html('<strong>Status: </strong>' + org.status))
                .append($('<li></li>').html('<strong>Type: </strong>' + org.type))
                .append($('<li></li>').html('<strong>Name: </strong><span class="orgname">' + org.name + "</span>"))
                .append($('<li></li>').html('<strong>Address: </strong><span class="orgaddress">' + org.address + "</span>"))
                .append($('<li></li>').html('<strong>City: </strong><span class="orgcity">' + org.city + "</span>"))
                .append($('<li></li>').html('<strong>Postal Code: </strong><span class="orgzip">' + org.zip + "</span>"))
                .append($('<li></li>').html('<strong>State: </strong><span class="orgstate">' +org.state + "</span>"));


            $('#orgContainer')
                .append(orgBox
                        .append(link)
                        .append($('<div></div>')
                                .append(actions)
                                .append(info)));
        }
    };


    $.ajax({
        success: function(data) {
            updateOrgs(data.payload);
        },
        url: '/org/org/',
        async: false,
        cache: false,
        dataType: 'json',
        statusCode: window.mobile_assets.statusCodes
    });

    var showLightbox = function(box, CB) {
        var lb = $(box),
        div = $(box + ' > div');

        lb.fadeIn('fast').css('top', $(window).scrollTop());

        // Center the lightbox in the window
        div.css({
            top: (lb.outerHeight() - div.outerHeight()) / 2,
            left: (lb.outerWidth() - div.outerWidth()) / 2
        });
        $.ajax({
            url: '/org/org/parent',
            type: 'GET',
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes,
            success: function(data) {
                data = data.payload
                var saveParent = $('#saveParentSelect');

                saveParent.children().remove();
                for(var i=0, len = data.length; i < len; i++) {
                    saveParent.append(
                        $('<option>').attr('value', data[i].id).text(data[i].name));
                }
            }
        });

    };

    var hideLightbox = function(e) {
        $('.lightbox').fadeOut('fast');
    };

    var showAddOrg= function(e) {
        showLightbox('.addBox');

        e.preventDefault();
    };

    var saveOrg = function(e) {
        $.ajax({
            url: '/org/org/',
            type: 'POST',
            success: function(data) {
                alert(data.message);
                window.location = window.location;
            },
            data: $('#orgForm').serializeArray(),
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });

        hideLightbox();
        e.preventDefault();
    };

    var modifyOrg= function(e) {
        $.ajax({
            success: function(data) {
                alert(data.message);
                window.location = window.location;
            },
            url: $(this).data('url'),
            type: 'POST',
            data: $('#editForm').serializeArray(),
            cache: false,
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes
        });

        hideLightbox();
        e.preventDefault();
    };


    // Shows the lightbox and dynamically adds the values of
    // the span elements to the input boxes
    var showEditOrg = function(e) {
        var $this = $(this),
        org = $('#' + $this.data('id'));

        showLightbox('.editBox');
        $('.modifyOrg').data('url', $(this).data('url'));

        $('#editForm input[type!=button]').each(function(i, e) {
            var $e = $(e),
            name = $e.attr('name');
            $e.val(org.find('.org' + name).text());
        });

        e.preventDefault();
    };

    // Bind the onclick events
    // By default, we want all of our divs to be collapsed
    $('.collapse').bind('click', window.mobile_assets.collapse).click();

    $('body').on('click', '.showAddOrg', showAddOrg);
    $('body').on('click', '.saveOrg', saveOrg);
    $('body').on('click', '.showEditOrg', showEditOrg);
    $('body').on('click', '.modifyOrg', modifyOrg);
    $('body').on('click', '.cancel', hideLightbox);
    
    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
    	$('#orgContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }
})();

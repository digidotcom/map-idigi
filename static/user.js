"use strict";
(function() {

    var setUp =  function() {
        var originalCleanUp = window.mobile_assets.statusCodes.cleanUp;
        function cleanUp(code) {
            if (code == 403) {
                $(".cancelAction").click();
            }
            originalCleanUp(code);
        }
        window.mobile_assets.statusCodes.cleanUp = cleanUp;
    }
    setUp();

    var showLightbox = function(box) {
            var lb = $(box),
            div = $(box + ' > div');

            lb.fadeIn('fast').css('top', $(window).scrollTop());

        // Center the lightbox in the window
            div.css({
                top: (lb.outerHeight() - div.outerHeight()) / 2,
                left: (lb.outerWidth() - div.outerWidth()) / 2
            });

            $('.saveUser').data('url', $(this).data('url'));

            $.ajax({
                url: '/user/user/group',
                type: 'GET',
                dataType: 'json',
                statusCode: window.mobile_assets.statusCodes,
                success: function(data) {
                    data = data.payload
                    var userGroups = $('.userGroupIds');

                    userGroups.children().remove();

                    for (var i = 0, len = data.length; i < len; i++) {
                        if (data[i] != 'base') {
                            $('<option>').text(data[i]).appendTo(userGroups);
                        }
                    }
                }
            });


    },
    hideLightbox = function() {
        $('.lightbox').fadeOut();
    },

    cancelAction = function(e) {
        hideLightbox();

        e.preventDefault();
    },

    showAddUser = function(e) {
        var newOptions = $()
        showLightbox('.addBox');

        e.preventDefault();
    },

    showEditUser = function(e) {
        var user = $('#' + $(this).data('id'));

        showLightbox('.editBox');
        $('.modifyUser').data('url', $(this).data('url'));

        $('#editForm input[type!=button]').each(function(i, e) {
            var $e = $(e),
            n = $e.attr('name');

            $e.val(user.find('.user' + n).text());
        });

        e.preventDefault();
    },

    saveUser = function(e) {
        var data = $('#userForm').serializeArray()

        $.ajax({
            url: '/user/user',
            type: 'POST',
            data: data,
            dataType: 'json',
            success: function(data) {
                //data = data.payload;
                alert(data.message);
                window.location = window.location;
            },
            statusCode: window.mobile_assets.statusCodes
        })

        hideLightbox();

        e.preventDefault();
    },

    modifyUser = function(e) {
        var data = $('#editForm').serializeArray()

        $.ajax({
            url: $('.modifyUser').data('url'),
            type: 'PUT',
            data: data,
            cache: false,
            dataType: 'json',
            success: function(data) {
                //data = data.payload;
                alert(data.message);
                window.location = window.location;
            },
            statusCode: window.mobile_assets.statusCodes
        })

        hideLightbox();
        e.preventDefault();
    },

    deactivateUser = function(e) {
        var $this = $(this);
        var parent = $this.parent();
        $.ajax({
            success: function() {
                $('#' + $this.data('user'))
                    .addClass('deactivated')
                $this = $this.removeClass('deactivateUser')
                    .addClass('activateUser')
                    .text('Activate')
                    .data('url', '/user/user/' + $this.data('user') + '/activate')
                    .appendTo(parent)
            },
            url: $(this).data('url'),
            type: 'PUT',
            data: 'userId=' + encodeURIComponent(JSON.stringify($(this).data('user'))),
            dataType: 'json',
            cache: false,
            statusCode: window.mobile_assets.statusCodes
        })
    },

    activateUser = function(e) {
        var $this = $(this);
        var parent = $this.parent();
        $.ajax({
            success: function() {
                $('#' + $this.data('user'))
                    .removeClass('deactivated');
                $this = $this.removeClass('activateUser')
                    .addClass('deactivateUser')
                    .text('Deactivate')
                    .data('url', '/user/user/' + $this.data('user') + '/deactivate')
                    .appendTo(parent);
            },
            url: $(this).data('url'),
            type: 'PUT',
            data: 'userId=' + encodeURIComponent(JSON.stringify($(this).data('user'))),
            dataType: 'json',
            cache: false,
            statusCode: window.mobile_assets.statusCodes
        })
    },

    loadUsers = function() {
        var success = function(data) {
            data = data['payload'];

            for (var i = 0, length = data.length; i < length; i++) {
                var user = data[i];
                var groups = '';

                groups = user['user_groups'].join(', ');
                var ul = $('<ul></ul>')
                    .append($('<li></li>')
                            .html('<strong>First Name:</strong> <span class="userfirst_name">' + user['first_name'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>Middle Name:</strong> <span class="usermiddle_name">' + user['middle_name'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>Last Name:</strong> <span class="userlast_name">' + user['last_name'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>Email:</strong> <span class="useremail">' + user['email'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>User Name:</strong> <span class="useruser_name">' + user['user_name'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>Organization ID:</strong> <span class="userorg_id">' + user['org_id'] + '</span>'))
                    .append($('<li></li>')
                            .html('<strong>User Groups:</strong> <span class="useruserGroupIds">' + groups + '</span>'));

                var editLink = $('<li></li>')
                    .append($('<a></a>')
                            .addClass('showEditUser')
                            .attr('href', '#')
                            .data('url', '/user/user/' + user['user_id'])
                            .data('id', user['user_id'])
                            .text('Edit'));

                var activationToggleLink = $('<li></li>')

                if (user['status'] == 1) {
                    activationToggleLink
                        .append($('<a></a>')
                                .attr('href', '#')
                                .data('user', user['user_id'])
                                .data('url', '/user/user/' + user['user_id'] + '/deactivate')
                                .addClass('deactivateUser')
                                .text('Deactivate'));
                } else {
                    activationToggleLink
                        .append($('<a></a>')
                                .attr('href', '#')
                                .data('user', user['user_id'])
                                .data('url', '/user/user/' + user['user_id'] + '/activate')
                                .addClass('activateUser')
                                .text('Activate'));
                }


                var actions = $('<ul></ul>')
                    .addClass('actions')
                    .append(editLink)
                    .append(activationToggleLink),
                innerDiv = $('<div></div>')
                    .append(actions)
                    .append(ul),
                collapse = $('<a></a>')
                    .addClass('collapse')
                    .attr('href', '')
                    .text( user['user_name'] ),

                _user = $('<div></div>');

                if (user['status'] != 1) {
                    _user.addClass('deactivated');
                } else {
                    _user.append(innerDiv);
                }

                _user.addClass('box')
                    .attr('id', user['user_id'])
                    .append(collapse)
                    .append(innerDiv)
                    .appendTo('#userContainer');
            }

        }


        $.ajax({
            url: '/user/user',
            type: 'GET',
            success: success,
            statusCode: window.mobile_assets.statusCodes,
            dataType: 'json',
            async: false,
        });

    };

    loadUsers();

    // Bind the onclick events
    // By default, we want all of our divs to be collapsed
    $('.collapse').bind('click', window.mobile_assets.collapse).click();

    $('.showAddUser').bind('click', showAddUser);
    $('.saveUser').bind('click', saveUser);
    $('body').on('click', '.modifyUser', modifyUser);
    $('body').on('click', '.activateUser', activateUser);
    $('body').on('click', '.deactivateUser', deactivateUser);
    $('body').on('click', '.showEditUser', showEditUser);
    $('.cancelAction').bind('click', cancelAction);
    
    //Workaround for IE8 not supported nth-child in css
    if($.browser.msie && parseInt($.browser.version, 10) < 9){
    	$('#userContainer > div:nth-child(odd)').addClass('ieCompatRow');
    }

})();

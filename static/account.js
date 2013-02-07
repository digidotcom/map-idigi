(function () {
    var showLightbox = function (box) {
        var lb = $(box),
        div = $(box + ' > div');

        lb.fadeIn('fast').css('top', $(window).scrollTop());

        // Center the lightbox in the window
        div.css({
            top: (lb.outerHeight() - div.outerHeight()) / 2,
            left: (lb.outerWidth() - div.outerWidth()) / 2
        });

    },
    hideLightbox = function () {
        $('.lightbox').fadeOut('fast');
    },
    showPassword = function (e) {
        showLightbox('.passwordBox');

        e.preventDefault();
    },
    savePassword = function () {
        $.ajax({
            url: '/account/security/password',
            type: 'PUT',
            data: $('#passwordForm').serializeArray(),
            statusCode: window.mobile_assets.statusCodes,
            dataType: 'json',
            success: function(data) {
                if (data.payload) {
                    alert('Password changed successfully');
                } else {
                    alert('Password change failed');
                }
            }
        })

        hideLightbox();
    },
    showQuestions = function (e) {
        showLightbox('.questionsBox');

        $.ajax({
            url: '/account/security/question',
            type: 'GET',
            statusCode: window.mobile_assets.statusCodes,
            dataType: 'json',
            success: function (data) {
                questions = data['payload'];

                for (question in questions) {
                    $('input[name=' + question + ']').val(questions[question])
                }
            },
            statusCode: window.mobile_assets.statusCodes
        });

        e.preventDefault();
    },
    saveQuestions = function () {
        $.ajax({
            url: '/account/security/question',
            type: 'PUT',
            data: $('#questionsForm').serializeArray(),
            dataType: 'json',
            statusCode: window.mobile_assets.statusCodes,
            success: function(data) {
                if (data.payload) {
                    alert('Security questions changed successfully');
                } else {
                    alert('Security question change failed: ' + data.message);
                }
            }
        });

        hideLightbox();
    },
    showResetPassword = function (e) {
        showLightbox('.resetBox');

        $.ajax({
            url: '/account/security/question',
            type: 'GET',
            statusCode: window.mobile_assets.statusCodes,
            dataType: 'json',
            success: function (data) {
                questions = data['payload'];

                for (question in questions) {
                    $('input[name=' + question + ']').val(questions[question])
                    $('label[for=' + question + ']').text(questions[question])
                }
            }
        });

        e.preventDefault();
    },
    resetPassword = function () {
        $.ajax({
            url: '/account/security/reset',
            type: 'PUT',
            data: $('#resetForm').serializeArray(),
            statusCode: window.mobile_assets.statusCodes,
            dataType: 'json',
            success: function(data) {
                if (data.payload) {
                    alert('Password reset successfully');
                } else {
                    alert('Password reset failed: ' + data.message);
                }
            }
        });
    };

    $('.savePassword').bind('click', savePassword);
    $('.showPassword').bind('click', showPassword);

    $('.saveQuestions').bind('click', saveQuestions);
    $('.showQuestions').bind('click', showQuestions);

    $('.resetPassword').bind('click', resetPassword);
    $('.showResetPassword').bind('click', showResetPassword);

    $('.cancelAccount').bind('click', hideLightbox);
})();

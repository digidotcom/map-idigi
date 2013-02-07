"use strict";

// Accepts three arguments: theUrl, successFunction, an optional errorHandler, and an optional http method (put, post, delete, get).
var ajaxRequest = function() {
        var xmlHttp = new XMLHttpRequest(),
            theUrl = arguments[0],
            success = arguments[1],
            method, error, defaultError = function(e) {
                alert('unable to open ' + theUrl);
            }

            // Parse our arguments to the function
            // We could do some more error checking here too
        if (arguments.length == 4) {
            error = arguments[2];
            method = arguments[3];
        } else if (arguments.length == 3) {
            method = "GET";
            error = arguments[2];
        } else {
            method = "GET";
            error = defaultError;
        }

        xmlHttp.open(method, theUrl, false);
        xmlHttp.onload = function(e) {
            if (this.status == 200) {
                success(JSON.parse(this.response));
            } else {
                error();
            }
        }

        // And off we go.
        xmlHttp.send(null);
    }

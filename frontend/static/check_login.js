

setInterval(function() {
    $.get('/check_session', function(data) {
        if (data.logged_in === false) {
            window.location.href = '/login';
        }
    });
}, 5000);

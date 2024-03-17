let statusMic;



function startEndListen() {
    var boton = document.getElementById("micButton");
    if (statusMic == null) {
        statusMic = 'start';
        boton.className = "btn btn-danger";

    }
    else if (statusMic == 'start') {
        statusMic = 'end';
        boton.className = "btn btn-primary";

    }
    else {
        statusMic = 'start';
        boton.className = "btn btn-danger";

    }

    $.ajax({
        url: '/',
        type: 'POST',
        data: {
           status: statusMic
        },
        success: function(response) {
            console.log(response);
        },
        error: function(error) {
            console.log(error);
        }
    })
}
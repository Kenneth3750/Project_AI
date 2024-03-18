let statusMic;

var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    console.log('Conectado al servidor SocketIO');
});

// Escuchar el evento enviado desde el servidor y mostrar la información en la página
socket.on('informacion_del_servidor', function(data) {
    console.log('Informacion del servidor recibida:', data.data);
    document.getElementById("status").innerHTML = `Status: ${data.data}`;
});


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
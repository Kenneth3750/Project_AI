let statusMic;

navigator.getUserMedia = (navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);


var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    console.log('Conectado al servidor SocketIO');
});

// Escuchar el evento enviado desde el servidor y mostrar la información en la página
socket.on('informacion_del_servidor', function(data) {
    console.log('Informacion del servidor recibida:', data.data);
    document.getElementById("status").innerHTML = `Status: ${data.data}`;
});

function toggleRecording() {
    let boton = document.getElementById("recordButton");

    if (boton.dataset.recording === "false" || !boton.dataset.recording) {
        boton.dataset.recording = "true";
        boton.textContent = "Detener Grabación";
        boton.className = "btn btn-danger";
        startRecording();
    } else {
        boton.dataset.recording = "false";
        boton.textContent = "Comenzar Grabación";
        boton.className = "btn btn-primary";
        stopRecording();
    }
}



let audioStream;
let mediaRecorder;
let chunks = [];

// Comenzar la grabación al presionar el botón "Comenzar Grabación"
async function startRecording() {
    chunks = [];
    try {
        // Solicitar permiso al usuario para acceder al micrófono
        const permission = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Si el permiso fue concedido, comenzar la grabación
        if (permission) {
            audioStream = permission;
            mediaRecorder = new MediaRecorder(audioStream);

            mediaRecorder.ondataavailable = function(e) {
                chunks.push(e.data);
            };

            mediaRecorder.onstop = function() {
                const audioBlob = new Blob(chunks, { 'type' : 'audio/wav' });
                sendAudio(audioBlob);
            };

            mediaRecorder.start();
        } else {
            console.error('El usuario denegó el acceso al micrófono.');
        }
    } catch (err) {
        console.error('Error al obtener acceso al micrófono:', err);
    }
}


// Detener la grabación y enviar el audio al presionar el botón "Detener Grabación y Enviar"
function stopRecording() {

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        audioStream.getTracks().forEach(track => track.stop());
    }

}

// Función para enviar el audio grabado a través de AJAX usando jQuery
function sendAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');

    $.ajax({
        url: '/audio',
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            console.log('Audio enviado correctamente:', data);
        },
        error: function(xhr, status, error) {
            console.error('Error al enviar el audio:', error);
        }
    });
}

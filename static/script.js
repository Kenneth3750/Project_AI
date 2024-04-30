let statusMic;
let silenceTimeout;
let audioStream;
let mediaRecorder;
let chunks = [];
let conversation;


const NO_SPEECH_DETECTED = 'No se detectó voz';

const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = false;
recognition.maxAlternatives = 1;


const synth = window.speechSynthesis;

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
    
});


function sendTranscript(formData) {
    $.ajax({
        url: '/audio',
        type: 'POST',
        data: formData,
        success: function(data) {
            console.log('Audio enviado correctamente:', data);
            if ('speechSynthesis' in window) {
                const synthesisUtterance = new SpeechSynthesisUtterance();
                synthesisUtterance.text = data.text;
                const voices = window.speechSynthesis.getVoices();
                synthesisUtterance.voice = voices[0];
                synthesisUtterance.onend = function(event) {
                    console.log('Finalizó la síntesis de voz:', event);
                    if (conversation){
                        recognition.start();
                        document.getElementById("status").innerHTML = `Status: Listening...`;
                    }
                };
                document.getElementById("status").innerHTML = `Status: Speaking...`;
                window.speechSynthesis.speak(synthesisUtterance);
            } else {
                console.log('Lo siento, tu navegador no soporta la API de síntesis de voz.');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error al enviar el audio:', error);

        }
    });

}



recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    console.log('Transcripción:', transcript);
    if (transcript){
        recognition.stop();
        document.getElementById("status").innerHTML = `Status: AI is thinking...`;

        let formData = {'user': transcript}
        if (conversation){
            sendTranscript(formData);
        }
    }
};


recognition.onerror = (e) => {
    console.error('Error en el reconocimiento de voz:', e.error);
    toggleRecording();
}




function toggleRecording() {
    let boton = document.getElementById("recordButton");

    if (boton.dataset.recording === "false" || !boton.dataset.recording) {
        boton.dataset.recording = "true";
        boton.dataset.conversation = "true";
        boton.textContent = "Detener Grabación";
        boton.className = "btn btn-danger";
        conversation = true;
        initConversation();
    } else {
        boton.dataset.recording = "false";
        boton.textContent = "Comenzar Grabación";
        boton.className = "btn btn-primary";
        boton.dataset.conversation = "false";
        conversation = false;
        stopRecording();
    }
}





// Detener la grabación y enviar el audio al presionar el botón "Detener Grabación y Enviar"
function stopRecording() {

    recognition.stop();
    document.getElementById("status").innerHTML = `Status: Sleeping...`;

    let boton = document.getElementById("recordButton");
    boton.dataset.recording = "false";
    boton.textContent = "Comenzar Grabación";
    boton.className = "btn btn-primary";
    $.ajax({
        url: '/save',
        type: 'POST',
        data: {"status": "save conversation"},
        success: function(data) {
            console.log('Audio enviado correctamente:', data);
  
        },
        error: function(xhr, status, error) {
            console.error('Error al enviar el audio:', error);

        }

    });
}


function initConversation() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();

            video.onloadedmetadata = function() {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;

                const context = canvas.getContext('2d');
                context.drawImage(video, 0, 0, canvas.width, canvas.height);

                canvas.toBlob((blob) => {
                    const formData = new FormData();
                    formData.append('image', blob, 'image.png');

                    $.ajax({
                        url: '/chat',
                        type: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            console.log('Image sent successfully:', data);
                            if(data.stop == "stop"){
                                stopRecording();
                            }else{
                                recognition.start();
                                document.getElementById("status").innerHTML = `Status: Listening...`;
                            }
                        },
                        error: function(xhr, status, error) {
                            console.error('Error sending image:', error);
                        }
                    });
                }, 'image/png');

                stream.getTracks().forEach(function(track) {
                    track.stop();
                });
            };
        })
        .catch(function(error) {
            console.error('Error accessing camera:', error);
        });
}




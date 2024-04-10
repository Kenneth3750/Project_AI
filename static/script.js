let statusMic;
let silenceTimeout;
let audioStream;
let mediaRecorder;
let chunks = [];
let conversation;


const NO_SPEECH_DETECTED = 'No se detectó voz';

// Comenzar la grabación al presionar el botón "Comenzar Grabación"

let audioContext = new AudioContext();
let analyser = audioContext.createAnalyser();

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


async function startRecordingLoop() {
    while (conversation) {
        try {
            const transcript = await startRecording();
            if (transcript !== NO_SPEECH_DETECTED) {
                console.log('Transcripción:', transcript);
                const formData = {'user': transcript};
                $.ajax({
                    url: '/audio',
                    type: 'POST',
                    data: formData,
                    success: function(data) {
                        console.log('Audio enviado correctamente:', data);
                        if ('speechSynthesis' in window) {
                            var synthesisUtterance = new SpeechSynthesisUtterance();
                            synthesisUtterance.text = data.text;
                            var voices = window.speechSynthesis.getVoices();
                            synthesisUtterance.voice = voices[0];
                            window.speechSynthesis.speak(synthesisUtterance);
                        } else {
                            console.log('Lo siento, tu navegador no soporta la API de síntesis de voz.');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error al enviar el audio:', error);
                    }
                });
            } else {
                console.log('No se detectó voz.');
            }
        } catch (error) {
            console.log('Error al iniciar el reconocimiento de voz:', error);
           
 
        }
    }
}




function toggleRecording() {
    let boton = document.getElementById("recordButton");

    if (boton.dataset.recording === "false" || !boton.dataset.recording) {
        boton.dataset.recording = "true";
        boton.dataset.conversation = "true";
        boton.textContent = "Detener Grabación";
        boton.className = "btn btn-danger";
        conversation = true;
        startRecordingLoop();
    } else {
        boton.dataset.recording = "false";
        boton.textContent = "Comenzar Grabación";
        boton.className = "btn btn-primary";
        boton.dataset.conversation = "false";
        conversation = false;
        stopRecording();
    }
}

// Comenzar la grabación al presionar el botón "Comenzar Grabación"
async function startRecording() {
    return new Promise(async (resolve, reject) => {
        let recognition = null;

    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.start();

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            resolve(transcript);

        };
        recognition.onerror = function(event) {
            console.error('Error en el reconocimiento de voz:', event.error);
            resolve(NO_SPEECH_DETECTED);
        };
    } else {
        console.log('Lo siento, tu navegador no soporta la API de reconocimiento de voz.');
    }
    recognition.onend = function() {
        resolve(NO_SPEECH_DETECTED);
    };
    });
}



// Detener la grabación y enviar el audio al presionar el botón "Detener Grabación y Enviar"
function stopRecording() {

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        audioStream.getTracks().forEach(track => track.stop());

    }

    let boton = document.getElementById("recordButton");
    boton.dataset.recording = "false";
    boton.textContent = "Comenzar Grabación";
    boton.className = "btn btn-primary";

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
            if ('speechSynthesis' in window) {
                var synthesisUtterance = new SpeechSynthesisUtterance();
                synthesisUtterance.text = data.text;
                var voices = window.speechSynthesis.getVoices();
                synthesisUtterance.voice = voices[0];
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

function isSilent(audioData) {
    const averageAmplitude = audioData.reduce((acc, val) => acc + val, 0) / audioData.length;
    const threshold = 128; // Umbral para considerar silencio
    return averageAmplitude < threshold;
}

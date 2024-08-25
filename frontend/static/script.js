let statusMic;
let silenceTimeout;
let audioStream;
let mediaRecorder;
let chunks = [];
let conversation;
let modal = document.getElementById("modal");

const NO_SPEECH_DETECTED = 'No se detectó voz';

const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = false;
recognition.maxAlternatives = 1;

document.addEventListener('DOMContentLoaded', () => {
    modal = document.getElementById("modal");
    if (modal){
        console.log('Modal:', modal);
    }
    else{
        console.log('No hay modal');
    }
});
const synth = window.speechSynthesis;

navigator.getUserMedia = (navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);


function sendTranscript(formData) {
    $.ajax({
        url: '/audio',
        type: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        data: formData,
        success: function(data) {
            console.log('Texto:', data.messages);
            console.log('Display:', data.display_responses);
            // if ('speechSynthesis' in window) {
            //     const synthesisUtterance = new SpeechSynthesisUtterance();
            //     synthesisUtterance.text = data.text;
            //     const voices = window.speechSynthesis.getVoices();
            //     synthesisUtterance.voice = voices[0];
            //     synthesisUtterance.onend = function(event) {
            //         console.log('Finalizó la síntesis de voz:', event);
            //         if (conversation){
            //             recognition.start();
            //             document.getElementById("status").innerHTML = `Status: Listening...`;
            //         }
            //     };
            //     document.getElementById("status").innerHTML = `Status: Speaking...`;
            //     window.speechSynthesis.speak(synthesisUtterance);
            // } else {
            //     console.log('Lo siento, tu navegador no soporta la API de síntesis de voz.');
            // }
            recognition.start();
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

        if (conversation){
            const event = new CustomEvent('chat', { detail: transcript });
            window.dispatchEvent(event);
            // sendTranscript(formData)

        }
    }
};

window.initRecognition = function() {
    if (conversation){
        recognition.start();
        document.getElementById("status").innerHTML = `Status: Listening...`;
    }
  };
  
window.stopRecognition = function() {
    stopRecording();
  };

recognition.onerror = (e) => {
    console.error('Error en el reconocimiento de voz:', e.error);
    
}




window.toggleRecording = function() {
    let boton = document.getElementById("recordButton");

    if (boton.dataset.recording === "false" || !boton.dataset.recording) {
        conversation = true;
        initConversation();
    } else {
        conversation = false;
        stopRecording();
    }
    window.dispatchEvent(new CustomEvent('recordingStatusChanged', { 
        detail: { isRecording: conversation } 
    }));
}





// Detener la grabación y enviar el audio al presionar el botón "Detener Grabación y Enviar"
function stopRecording() {
    recognition.stop();
    document.getElementById("status").innerHTML = `Status: Sleeping...`;

    const event = new CustomEvent('chat', { detail: "goodbye" });
    window.dispatchEvent(event);

    window.dispatchEvent(new CustomEvent('recordingStatusChanged', { 
        detail: { isRecording: false } 
    }));

    let boton = document.getElementById("recordButton");
    boton.dataset.recording = "false";
    boton.textContent = "Start conversation";
    boton.className = "btn btn-primary";
    $.ajax({
        url: '/save',
        type: 'POST',
        data: {"status": "save conversation", "role_id": getRoleId()},
        success: function(data) {
            console.log('Audio enviado correctamente:', data);
        },
        error: function(xhr, status, error) {
            console.error('Error al enviar el audio:', error);
        }
    });
}

function getRoleId() {
    const path = window.location.pathname;
    const parts = path.split('/');
    return parts[parts.length - 1];
}

function initConversation() {
    window.dispatchEvent(new CustomEvent('modalVisibilityChanged', { detail: { visible: true } }));
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {

            role_id = getRoleId();
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
                        url: `/chat/${role_id}`,
                        type: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            window.dispatchEvent(new CustomEvent('modalVisibilityChanged', { detail: { visible: false } }));
                            console.log('Image sent successfully');
                            name = data.name;
                            document.getElementById("user_name").innerHTML = "Current user: " + name;
                            if(data.stop == "stop"){
                                stopRecording();
                            }else{
                                if (conversation){
                                    const event = new CustomEvent('chat', { detail: "welcome" });
                                    window.dispatchEvent(event);
                                    

                                }
                            }
                        },
                        error: function(xhr, status, error) {
                            window.dispatchEvent(new CustomEvent('modalVisibilityChanged', { detail: { visible: false } }));
                            console.error('Error sending image:', error);
                            stopRecording();
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

window.getRoleId = getRoleId;
window.initConversation = initConversation;
window.stopRecording = stopRecording;

const CHAT_OPEN_KEY = 'isAnyChatOpen';

function isChatURL() {
    return window.location.pathname.startsWith('/chat/');
}

window.addEventListener('beforeunload', function () {
    if (isChatURL()) {
        localStorage.removeItem(CHAT_OPEN_KEY);
    }
});

document.addEventListener('DOMContentLoaded', function () {
    if (isChatURL()) {
        if (localStorage.getItem(CHAT_OPEN_KEY)) {
            alert("Ya tienes abierta una sección del chat en otra pestaña. Cierra la otra pestaña primero.");
            window.location.href = '/';  // Redirige a la página de inicio
        } else {
            localStorage.setItem(CHAT_OPEN_KEY, 'true');
        }
    }
});

let statusMic;
let silenceTimeout;
let audioStream;
let mediaRecorder;
let chunks = [];
let conversation;
let globalTranscript = null;
let modal = document.getElementById("modal");

const NO_SPEECH_DETECTED = 'No se detectó voz';

const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = false;
recognition.maxAlternatives = 1;

function updateAvatarState(newState) {
    window.dispatchEvent(new CustomEvent('avatarStatusChanged', { detail: { status: newState } }));
  }

const synth = window.speechSynthesis;

navigator.getUserMedia = (navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);


recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    globalTranscript = transcript;
    console.log('Transcripción:', transcript);
    if (transcript){
        recognition.stop();
        window.dispatchEvent(new CustomEvent('audioStatusChanged', { detail: { isPlaying: true } }));
        updateAvatarState("Thinking");

        if (conversation){
            const event = new CustomEvent('chat', { detail: transcript });
            window.dispatchEvent(event);
        }
        else {
            recognition.stop();
            globalTranscript = null;
            window.dispatchEvent(new CustomEvent('audioStatusChanged', { detail: { isPlaying: false } }));
            updateAvatarState("Sleeping");
        }
    }
};

window.initRecognition = function() {
    if (conversation){
        recognition.start();
        globalTranscript = null;
        updateAvatarState("Listening");
    }
    else{
        updateAvatarState("Sleeping");
    }
  };
  
window.initRecognitionImage = function() {
    if (conversation){
        recognition.start();
        globalTranscript = null;
        updateAvatarState("Listening");
        captureAndSendImage();
    }
    else{
        updateAvatarState("Sleeping");
    }
  };
  

window.stopRecognition = function() {
    stopRecording();
  };

recognition.onerror = (e) => {
    console.log('Error en el reconocimiento de voz:', e.error);
    
}

recognition.onend = (e) => {
    console.log('Fin del reconocimiento de voz');
    setTimeout(() => { console.log('Fin del reconocimiento de voz'); }, 1000);
    if (conversation && globalTranscript === null){
        recognition.start();
    }
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
    globalTranscript = null;

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
                            user_name = data.name;
                            document.getElementById("user_name").innerHTML = "Current user: " + user_name;
                            window.localStorage.setItem("user_name", user_name);
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


function captureAndSendImage() {
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
                        url: `/saveCurrent`, 
                        type: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            console.log('Image sent successfully');
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
  

window.getRoleId = getRoleId;
window.initConversation = initConversation;
window.stopRecording = stopRecording;




function updateNaiaRole() {
    const roleId = window.getRoleId();
    console.log('Role ID:', roleId);
    
    let roleName;
    switch(roleId) {
      case "1": roleName = "Investigator"; window.localStorage.setItem("role", "1"); break;
      case "2": roleName = "Recepcionist"; window.localStorage.setItem("role", "2"); break;
      case "3": roleName = "Personal Skills Trainer"; window.localStorage.setItem("role", "3"); break;
      case "4": roleName = "Personal Assistant"; window.localStorage.setItem("role", "4"); break;
      case "5": roleName = "University Guide"; window.localStorage.setItem("role", "5"); break;
      default: roleName = "Unknown Role";
    }
  
    window.dispatchEvent(new CustomEvent('naiaRoleUpdated', { detail: { role: roleName } }));
    console.log('NAIA role updated to:', roleName);
  }

  function initializeNaiaRole() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', updateNaiaRole);
    } else {
      updateNaiaRole();
    }
  }

document.addEventListener('DOMContentLoaded', function () {

    window.addEventListener('reactComponentReady', initializeNaiaRole);
    initializeNaiaRole();

});


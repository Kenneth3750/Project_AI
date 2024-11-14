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

function showNotification(message, type) {
  const notificationDiv = document.createElement('div');
  notificationDiv.textContent = message;
  notificationDiv.className = `notification ${type}`;
  document.body.appendChild(notificationDiv);
  setTimeout(() => {
      notificationDiv.remove();
  }, 3000);
}


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
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          showNotification('getUserMedia is not supported in this browser. Please use a modern browser like Chrome', 'error');
          return;
        }
        conversation = true;
        window.localStorage.setItem("conversation", "true");
        initConversation();
    } else {
        conversation = false;
        window.localStorage.setItem("conversation", "false");
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

    window.dispatchEvent(new CustomEvent('audioStatusChanged', { detail: { isPlaying: false } }));

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
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error('getUserMedia is not supported in this browser');
      showNotification('getUserMedia is not supported in this browser. Please use a modern browser like Chrome', 'error');
      return;
    }
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
            showNotification('Error accessing camera. Please allow camera access and try again. Verify that all permissions are granted and that other applications are not using the camera.', 'error');
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


async function getUserLocation() {
      if (!navigator.geolocation) {
        console.error('Geolocation is not supported by this browser.');
        showNotification('Geolocation is not supported by this browser.', 'error');
        return null;
    }
    try {
      const storedLocation = window.localStorage.getItem("user_location");
      const locationDate = window.localStorage.getItem("location_date");
      const currentDate = new Date();
  
      if (storedLocation && locationDate) {
        const lastUpdateDate = new Date(locationDate);
        if (currentDate - lastUpdateDate < 86400000) { // 24 horas en milisegundos
          console.log('Usando ubicación almacenada');
          return JSON.parse(storedLocation);
        }
      }
  
      const position = await new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('Geolocalización no soportada por este navegador.'));
        } else {
          navigator.geolocation.getCurrentPosition(resolve, reject);
        }
      });
  
      const { latitude, longitude } = position.coords;

      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
      const data = await response.json();
  
      const cleanCityName = (cityName) => {
        const unwantedPrefixes = ['Perímetro Urbano', 'Área Metropolitana', 'Zona Urbana'];
        let cleanName = cityName;
        for (const prefix of unwantedPrefixes) {
          if (cleanName.startsWith(prefix)) {
            cleanName = cleanName.substring(prefix.length).trim();
          }
        }
        return cleanName.split(' ')[0];
      };
  
      const rawCityName = data.address.city || data.address.town || data.address.village || 'Desconocido';
      const cleanedCityName = cleanCityName(rawCityName);
  
      const locationData = {
        latitude,
        longitude,
        city: cleanedCityName,
        country: data.address.country || 'Desconocido'
      };
  
      window.localStorage.setItem("user_location", JSON.stringify(locationData));
      window.localStorage.setItem("location_date", currentDate.toISOString());
  
      return locationData;
    } catch (error) {
      console.error('Error al obtener la ubicación:', error);
      throw error;
    }
  }




function updateNaiaRole() {
    const roleId = window.getRoleId();
    console.log('Role ID:', roleId);
    
    let roleName;
    switch(roleId) {
      case "1": roleName = "Researcher"; window.localStorage.setItem("role", "1"); break;
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
    getUserLocation()
    .then((location) => {
      console.log('Ubicación del usuario:', location);
      $.ajax({
        url: '/saveLocation',
        type: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        data: JSON.stringify(location),
        success: function(data) {
          console.log('Ubicación enviada correctamente:', data);
        },
        error: function(xhr, status, error) {
          console.error('Error al enviar la ubicación:', error);
        }
      });
    })
    .catch((error) => {
      console.error('Error al obtener la ubicación:', error.message);
    });

});


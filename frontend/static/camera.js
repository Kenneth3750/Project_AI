const video = document.getElementById('video');
const captureBtn = document.getElementById('capture-btn');
const takeBtn = document.getElementById('take-btn');
const erase = document.getElementById('erase');
const upload = document.getElementById('upload-btn');
const myImage = document.getElementById('myImage');
const videoImageContainer = document.getElementById('video-image-container');
let reader;
let image;


function showNotification(message, type) {
    const notificationDiv = document.createElement('div');
    notificationDiv.textContent = message;
    notificationDiv.className = `notification ${type}`;
    document.body.appendChild(notificationDiv);
    setTimeout(() => {
        notificationDiv.remove();
    }, 3000);
}

function stopCamera() {
    if (video.srcObject) {
        const tracks = video.srcObject.getTracks();
        tracks.forEach(function(track) {
            track.stop();
        });
    }
    video.srcObject = null;
    video.style.display = 'none';
    captureBtn.style.display = 'none';
    closeCameraBtn.style.display = 'none';
}

// New button to close the camera
const closeCameraBtn = document.createElement('button');
closeCameraBtn.textContent = 'Close camera';
closeCameraBtn.className = 'btn-naia';
closeCameraBtn.style.display = 'none';
videoImageContainer.appendChild(closeCameraBtn);

closeCameraBtn.addEventListener('click', () => {
    stopCamera();
    erase.style.display = 'none';
});

takeBtn.addEventListener('click', () => {
    video.style.display = 'block';
    erase.style.display = 'inline';
    captureBtn.style.display = 'block';
    closeCameraBtn.style.display = 'inline';
    myImage.style.display = 'none';
    
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(error => {
            console.error('Error accessing camera: ', error);
        });
});

captureBtn.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const previousImage = document.getElementById('captured-image');
    if (previousImage) {
        previousImage.remove();
    }

    const image = new Image();
    image.src = canvas.toDataURL();
    image.id = 'captured-image';
    myImage.src = image.src;
    
    stopCamera();
    myImage.style.display = 'block';
});

document.getElementById('send').addEventListener('click', () => {
    const personName = document.getElementById('person_name').value;
    
    if (myImage.style.display !== "none" && personName !== "") {
        const dataURL = myImage.src;
        const byteString = atob(dataURL.split(',')[1]);
        const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const uint8Array = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([arrayBuffer], {type: mimeString});

        const formData = new FormData();
        formData.append('image', blob);
        formData.append('personName', personName);

        $.ajax({
            url: '/home',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log('Image sent successfully:', data);
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification("Image sent successfully", 'success');
                    stopCamera();
                    myImage.style.display = 'none';
                    erase.style.display = 'none';
                    document.getElementById('person_name').value = "";
                    
                    // Add the new user to the list
                    addUserToList(personName);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error sending the image:', error);
                showNotification('Error sending the image. Please try again.', 'error');
            }
        });
    } else {
        showNotification('Please take a picture and enter your name', 'error');
    }
});


function addUserToList(username) {
    const userList = document.getElementById('userList');
    if (userList) {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.textContent = username;
        li.onclick = () => showUserDetails(username);
        userList.appendChild(li);
    } else {
        console.error('User list element not found');
    }
}

function goToChat() {
    var role = document.getElementById('select-role').value;
    window.location.href = '/chat/' + role;
}

erase.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    const previousImage = document.getElementById('captured-image');
    if (previousImage) {
        previousImage.remove();
    }

    stopCamera();
    myImage.src = "";
    myImage.style.display = 'none';
    erase.style.display = 'none';
});

upload.addEventListener('click', () => {
    const previousImage = document.getElementById('captured-image');
    if (previousImage) {
        previousImage.remove();
    }

    stopCamera();

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/png, image/jpeg';
    erase.style.display = 'inline';
    
    fileInput.onchange = () => {
        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = () => {
            const image = new Image();
            image.src = reader.result;
            image.id = 'captured-image';
            myImage.style.display = 'block';
            myImage.src = image.src;
            
            image.onload = () => {
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');

                canvas.width = image.width;
                canvas.height = image.height;
                context.drawImage(image, 0, 0, canvas.width, canvas.height);

                const dataURL = canvas.toDataURL(file.type);
                const byteString = atob(dataURL.split(',')[1]);
                const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
                const arrayBuffer = new ArrayBuffer(byteString.length);
                const uint8Array = new Uint8Array(arrayBuffer);
                for (let i = 0; i < byteString.length; i++) {
                    uint8Array[i] = byteString.charCodeAt(i);
                }
                const blob = new Blob([arrayBuffer], { type: mimeString });

                const formData = new FormData();
                formData.append('image', blob);
                formData.append('personName', personName);
            };

            fileInput.remove();
        };

        reader.readAsDataURL(file);
    };

    fileInput.click();
});
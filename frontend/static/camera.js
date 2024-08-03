const video = document.getElementById('video');
const captureBtn = document.getElementById('capture-btn');
const takeBtn = document.getElementById('take-btn');
const erase = document.getElementById('erase');
const upload = document.getElementById('upload-btn');
const myImage = document.getElementById('myImage');
let reader;
let image;

takeBtn.addEventListener('click', () => {
    // Show the video element
    video.style.display = 'block';
    erase.style.display = 'inline';
    video.style.width = '100%';
    captureBtn.style.display = 'block';
    // Request access to the camera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(error => {
            console.error('Error accessing camera: ', error);
        });
});



// Capturar la foto cuando se hace clic en el botón
captureBtn.addEventListener('click', () => {
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');

    // Ajustar el tamaño del canvas al tamaño del video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Dibujar el video en el canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Eliminar la imagen anterior si existe
    const previousImage = document.getElementById('captured-image');
    if (previousImage) {
        previousImage.remove();
    }

    // Mostrar la imagen capturada en pantalla
    const image = new Image();
    myImage.style.display = 'block';
    image.src = canvas.toDataURL();
    image.id = 'captured-image';
    myImage.src = image.src;
});

document.getElementById('send').addEventListener('click', () => {

    const personName = document.getElementById('person_name').value;
    console.log(myImage.src)
    console.log(personName)
    if ( myImage.style.display !== "none"  && personName !== "") {
        // Convertir la URL de datos en un Blob
        const dataURL = myImage.src;
        const byteString = atob(dataURL.split(',')[1]);
        const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const uint8Array = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([arrayBuffer], {type: mimeString});

        // Crear objeto FormData con la imagen y el nombre de la persona
        const formData = new FormData();
        formData.append('image', blob);
        formData.append('personName', personName);

        // Enviar los datos al servidor usando AJAX de jQuery
        $.ajax({
            url: '/home',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                console.log('Imagen enviada correctamente:', data);
                if (data.error) {
                    alert(data.error);
                } else {
                    alert('Imagen enviada correctamente.');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error al enviar la imagen:', error);
            }
        })
    }else{
        alert('Por favor, capture una imagen y escriba el nombre de la persona.');
    }
});

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



    if (video.srcObject) {
        const tracks = video.srcObject.getTracks();
        tracks.forEach(function(track) {
            track.stop();
        });
    }

    video.srcObject = null;
    myImage.src = "";
    myImage.style.display = 'none';
    video.style.display = 'none';
    captureBtn.style.display = 'none';

    erase.style.display = 'none';
});


upload.addEventListener('click', () => {

    const previousImage = document.getElementById('captured-image');
    if (previousImage) {
        previousImage.remove();
    }


    if (video.srcObject) {
        const tracks = video.srcObject.getTracks();
        tracks.forEach(function(track) {
            track.stop();
        });
    }

    video.srcObject = null;


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
                const lastImage = document.getElementById('captured-image');
            };

            fileInput.remove();
        };

        reader.readAsDataURL(file);
    };

    fileInput.click();
});






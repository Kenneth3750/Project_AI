// Acceder al video y al botón de captura
const video = document.getElementById('video');
const captureBtn = document.getElementById('capture-btn');

// Obtener acceso a la cámara
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(error => {
        console.error('Error al acceder a la cámara: ', error);
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

    // Mostrar la imagen capturada en pantalla
    const image = new Image();
    image.src = canvas.toDataURL();
    document.body.appendChild(image);
});

document.getElementById('send').addEventListener('click', () => {
    const images = document.getElementsByTagName('img');
    const lastImage = images[images.length - 1];
    const personName = document.getElementById('person_name').value;

    if (lastImage && personName) {
        // Convertir la URL de datos en un Blob
        const dataURL = lastImage.src;
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
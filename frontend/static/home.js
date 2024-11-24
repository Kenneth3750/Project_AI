async function requestDevicePermissions() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
        });
        
        console.log('Permisos concedidos para cámara y micrófono');
        
        stream.getTracks().forEach(track => track.stop());
        
        return true;
    } catch (error) {
        console.error('Error al solicitar permisos:', error);
        return false;
    }
}


requestDevicePermissions()
    .then(resultado => {
        if(resultado) {
            console.log('Permisos concedidos exitosamente');
        } else {
            console.log('No se pudieron obtener los permisos');
        }
    });



function sendApartment() {
    const apartmentNumber = document.getElementById("apartment-number").value.trim();
    const apartmentPhone = document.getElementById("apartment-phone").value.trim();

    if (!apartmentNumber || !apartmentPhone) {
        showNotification("Please fill in all fields.", "error");
        return;
    }

    const data = { apartmentNumber, apartmentPhone };
    $.ajax({
        url: '/apartment',
        type: 'POST',
        headers: { "Content-Type": "application/json" },
        data: JSON.stringify(data),
        success: function(response) {
            console.log('Apartment registered successfully');
            document.getElementById("apartment-number").value = "";
            document.getElementById("apartment-phone").value = "";
            showNotification("Apartment registered successfully", "success");
            getApartmentInfo();
        },
        error: function(xhr, status, error) {
            console.error('Error registering apartment:', error);
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
            showNotification("Error registering apartment: " + errorMessage, "error");
        }
    });
}

function getApartmentInfo() {
    $.ajax({
        url: '/apartment',
        type: 'GET',
        success: function(data) {
            const listApartment = document.getElementById("listApartments");
            listApartment.innerHTML = "";
            Object.entries(data).forEach(([apartmentNumber, apartmentPhone]) => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    <span>Apt ${apartmentNumber}: ${formatPhoneNumber(apartmentPhone)}</span>
                    <button class="btn btn-sm btn-danger" onclick="deleteApartment('${apartmentNumber}')">Delete</button>
                `;
                listApartment.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting apartment info:', error);
            showNotification("Error retrieving apartment information", "error");
        }
    });
}

function deleteApartment(apartmentNumber) {
    if (confirm(`Are you sure you want to delete apartment ${apartmentNumber}?`)) {
        $.ajax({
            url: `/apartment`,
            type: 'DELETE',
            headers: { "Content-Type": "application/json" },
            data: JSON.stringify({"apartmentNumber": apartmentNumber}),
            success: function(response) {
                showNotification(`Apartment ${apartmentNumber} deleted successfully`, "success");
                getApartmentInfo();
            },
            error: function(xhr, status, error) {
                console.error('Error deleting apartment:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
                showNotification("Error deleting apartment: " + errorMessage, "error");
            }
        });
    }
}

function formatPhoneNumber(phoneNumber) {
    return phoneNumber.replace(/(\d{2})(\d{3})(\d{3})(\d{4})/, '+$1 $2 $3 $4');
}

// Assume this function is called elsewhere to populate reservations
function getReservations() {
    $.ajax({
        url: '/reservations',
        type: 'GET',
        success: function(data) {
            const listReservations = document.getElementById("listReservations");
            listReservations.innerHTML = "";
            data.reservation.forEach(reservation => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `<strong>${reservation.user_name}</strong> - ${reservation.place}<br>
                                Date: ${reservation.reservation_date}, ${reservation.start_time} to ${reservation.end_time}`;
                listReservations.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting reservations:', error);
            showNotification("Error retrieving reservations", "error");
        }
    });
}


function sendEmailInfo() {
    const email = document.getElementById("person-email").value.trim();
    const personName = document.getElementById("person-name").value.trim();

    if (!email || !personName) {
        showNotification("Please fill in both name and email fields.", "error");
        return;
    }

    const existingContacts = Array.from(document.querySelectorAll('#listPeopleEmail li strong'))
        .map(nameElement => nameElement.textContent.trim());

    const nameExists = existingContacts.some(existingName => 
        existingName.toLowerCase() === personName.toLowerCase()
    );

    if (nameExists) {
        showNotification("A contact with this name already exists. Please use a different name.", "error");
        return;
    }

    $.ajax({
        url: '/email',
        type: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        data: JSON.stringify({"email": email, "name": personName}),
        success: function(response) {
            console.log('Contact added successfully');
            document.getElementById("person-email").value = "";
            document.getElementById("person-name").value = "";
            showNotification("Contact added successfully", "success");
            getEmailInfo();
        },
        error: function(xhr, status, error) {
            console.error('Error adding contact:', error);
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
            showNotification("Error adding contact: " + errorMessage, "error");
        }
    });
}

function getEmailInfo() {
    $.ajax({
        url: '/email',
        type: 'GET',
        success: function(data) {
            const listEmails = document.getElementById("listPeopleEmail");
            listEmails.innerHTML = "";
            Object.entries(data).forEach(([name, email]) => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `
                    <span><strong>${name}</strong><br>${email}</span>
                    <button class="delete-btn" onclick="deleteContact('${name}', '${email}')">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                listEmails.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting contact info:', error);
            showNotification("Error retrieving contact information", "error");
        }
    });
}

function deleteContact(name, email) {
    if (confirm(`Are you sure you want to delete the contact: ${name} (${email})?`)) {
        $.ajax({
            url: '/email',
            type: 'DELETE',
            headers: {
                "Content-Type": "application/json",
            },
            data: JSON.stringify({"name": name, "email": email}),
            success: function(data) {
                console.log('Contact deleted successfully');
                showNotification("Contact deleted successfully", "success");
                getEmailInfo();
            },
            error: function(xhr, status, error) {
                console.error('Error deleting contact:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
                showNotification("Error deleting contact: " + errorMessage, "error");
            }
        });
    }
}

function deleteEmail() {
    if (confirm("Are you sure you want to update the assistant's email? This will remove the current email.")) {
        $.ajax({
            url: '/email',
            type: 'DELETE',
            success: function(data) {
                console.log('Email updated successfully');
                showNotification("Assistant's email has been updated. Please set a new email in the chat.", "success");
                getEmailInfo();  // Refresh the list
            },
            error: function(xhr, status, error) {
                console.error('Error updating email:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
                showNotification("Error updating email: " + errorMessage, "error");
            }
        });
    }
}

function getSummaryPDF() {
    fetch('/trainer')
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.text();
        })
        .then(content => {
            console.log('Contenido recibido:', content);
            if (content.trim() === '') {
                throw new Error('No summary available');
            }

            const container = document.createElement('div');
            container.innerHTML = content;

            const doc = new jspdf.jsPDF();


            doc.setFontSize(18);
            doc.text('Resumen de Entrenamiento de Idiomas', 14, 20);

            const h2 = container.querySelector('h2');
            if (h2) {
                doc.setFontSize(14);
                doc.text(h2.textContent, 14, 30);
            }

            doc.setFontSize(12);
            let yOffset = 40;

            const progressList = container.querySelector('ul');
            if (progressList) {
                doc.text('Progreso en el último mes:', 14, yOffset);
                yOffset += 10;
                progressList.querySelectorAll('li').forEach(li => {
                    doc.text('• ' + li.textContent, 20, yOffset);
                    yOffset += 7;
                });
            }


            const tasksList = container.querySelector('ol');
            if (tasksList) {
                yOffset += 5;
                doc.text('Tareas para la próxima semana:', 14, yOffset);
                yOffset += 10;
                tasksList.querySelectorAll('li').forEach((li, index) => {
                    doc.text((index + 1) + '. ' + li.textContent, 20, yOffset);
                    yOffset += 7;
                });
            }

            doc.save('training_summary.pdf');
            console.log('PDF generado exitosamente');
        })
        .catch(error => {
            console.error('Error detallado:', error);
            if (error.error) {
                showNotification(error.error, 'error');
            } else if (error.message === 'No summary available') {
                showNotification('No training summary available yet.', 'info');
            } else {
                showNotification('An error occurred while generating the PDF. Please try again.', 'error');
            }
        });
}

function getInvestigatorPDF() {
    fetch('/investigator')
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.text();
    })
    .then(content => {
        console.log('Contenido recibido:', content);
        if (content.trim() === '') {
            throw new Error('No summary available');
        }

        const container = document.createElement('div');
        container.innerHTML = content;

        const doc = new jspdf.jsPDF();
        let yOffset = 10;
        const pageWidth = doc.internal.pageSize.getWidth();

        function addText(text, fontSize = 12, isBold = false) {
            doc.setFontSize(fontSize);
            doc.setFont(undefined, isBold ? 'bold' : 'normal');
            const lines = doc.splitTextToSize(text, pageWidth - 20);
            doc.text(lines, 10, yOffset);
            yOffset += (lines.length * fontSize * 0.352) + 5;
            if (yOffset > 280) {
                doc.addPage();
                yOffset = 10;
            }
        }

        const h1 = container.querySelector('h1');
        if (h1) addText(h1.textContent, 18, true);

        container.querySelectorAll('p, h2').forEach(element => {
            if (element.tagName === 'H2') {
                addText(element.textContent, 14, true);
            } else {
                addText(element.textContent);
            }
        });

        doc.save('research_summary.pdf');
        console.log('PDF generado exitosamente');
    })
    .catch(error => {
        console.error('Error detallado:', error);
        if (error.error) {
            showNotification(error.error, 'error');
        } else if (error.message === 'No summary available') {
            showNotification('No research summary available yet.', 'info');
        } else {
            showNotification('An error occurred while generating the PDF. Please try again.', 'error');
        }
    });
}


function showNotification(message, type) {
    const notificationDiv = document.createElement('div');
    notificationDiv.textContent = message;
    notificationDiv.className = `notification ${type}`;
    document.body.appendChild(notificationDiv);
    setTimeout(() => {
        notificationDiv.remove();
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        z-index: 1000;
    }
    .notification.success {
        background-color: #28a745;
    }
    .notification.error {
        background-color: #dc3545;
    }
`;
document.head.appendChild(style);

function getUserInfo() {
    fetch('/user-info')
        .then(response => response.json())
        .then(data => {
            if (data && data.name) {
                document.getElementById('user-name').textContent = data.name;
            } else {
                document.getElementById('user-name').textContent = 'User';
            }
            if (data && data.image) {
                document.getElementById('user-image').src = data.image;
            } else {
                document.getElementById('user-image').src = '/static/img/no_user.png';
            }
            if (data && data.given_name) {
                document.getElementById('welcome-message').textContent = `Welcome to NAIA, ${data.given_name}!`;
            }else{
                document.getElementById('welcome-message').textContent = `Welcome to NAIA!`;
            }
        })
        .catch(error => {
            console.error('Error fetching user info:', error);
            document.getElementById('user-name').textContent = 'User';
            document.getElementById('user-image').src = '/static/default-avatar.png';
            document.getElementById('welcome-message').alt = 'Welcome!';
        });
}

function logout() {
    fetch('/logout', {
        method: 'POST',
        credentials: 'same-origin'
    }).then(() => {
        console.log('Logged out');
    }).catch(error => console.error('Error during logout:', error));
}


function getPdfFilename(){
    $.ajax({
        url: '/pdfreader',
        type: 'GET',
        success: function(data) {
            console.log('Pdf filename retrieved successfully');
            if (data.pdf_filename != null){
                window.localStorage.setItem("pdfFilename", data.pdf_filename);
            }else{
                window.localStorage.setItem("pdfFilename", null);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error getting pdf filename:', error);
            window.localStorage.setItem("pdfFilename", null);
        }
    });
    console.log(window.localStorage.getItem("pdfFilename"));
}

function addCommonArea() {
    const commonAreaName = document.getElementById('common-area-name').value.trim();
    if (commonAreaName) {
        const listCommonAreas = document.getElementById('listCommonAreas');
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.textContent = commonAreaName;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.onclick = function() {
            listCommonAreas.removeChild(li);
            deleteArea(commonAreaName);
        };
        
        li.appendChild(deleteBtn);
        listCommonAreas.appendChild(li);
        
        document.getElementById('common-area-name').value = '';
        
        $.ajax({
            url: '/areas',
            type: 'POST',
            headers: { 'Content-Type': 'application/json' },
            data: JSON.stringify({ "area": commonAreaName }),
            success: function(response) {
                console.log('Common area added successfully');
                showNotification('Common area added successfully', 'success');
            },
            error: function(xhr, status, error) {
                console.error('Error adding common area:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error';
                showNotification('Error adding common area: ' + errorMessage, 'error');
            }
        });  
    } else {
        alert('Please enter a name for the common area.');
    }
}

function getCommonAreas(){
    $.ajax({
        url: '/areas',
        type: 'GET',
        success: function(data) {
            const listCommonAreas = document.getElementById('listCommonAreas');
            listCommonAreas.innerHTML = '';
            console.log(data.areas);
            data.areas.forEach(area => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.textContent = area;
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn btn-sm btn-danger';
                deleteBtn.innerHTML = '&times;';
                deleteBtn.onclick = function() {
                    listCommonAreas.removeChild(li);
                    deleteArea(area);
                };
                
                li.appendChild(deleteBtn);
                listCommonAreas.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting common areas:', error);
            showNotification('Error retrieving common areas', 'error');
        }
    });
}

function deleteArea(area){
    $.ajax({
        url: '/areas',
        type: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        data: JSON.stringify({ "area": area }),
        success: function(response) {
            console.log('Common area deleted successfully');
            showNotification('Common area deleted successfully', 'success');
            getCommonAreas();
        },
        error: function(xhr, status, error) {
            console.error('Error deleting common area:', error);
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error';
            showNotification('Error deleting common area: ' + errorMessage, 'error');
        }
    });
}


function getRegisteredUsers() {
    $.ajax({
        url: '/users',
        type: 'GET',
        success: function(data) {
            const userList = document.getElementById('userList');
            userList.innerHTML = '';
            data.forEach(user => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.textContent = user;
                li.onclick = () => showUserDetails(user);
                userList.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting registered users:', error);
            showNotification("Error retrieving registered users", "error");
        }
    });
}

function showUserDetails(username) {
    $.ajax({
        url: `/users/${username}`,
        type: 'GET',
        success: function(data) {
            if (data.photo) {
                const base64Image = `data:image/jpeg;base64,${data.photo}`;
                document.getElementById('userPhoto').src = base64Image;
            } else {
 
                document.getElementById('userPhoto').src = '/static/img/default-user.jpg';
                console.warn(`No photo data for user: ${username}`);
            }
            
            document.getElementById('editName').value = username;
            document.getElementById('userDetailsModalLabel').textContent = `User: ${username}`;
            

            document.getElementById('saveNameBtn').onclick = () => updateUsername(username);
            document.getElementById('deleteUserBtn').onclick = () => deleteUser(username);
            

            new bootstrap.Modal(document.getElementById('userDetailsModal')).show();
        },
        error: function(xhr, status, error) {
            console.error('Error getting user details:', error);
            showNotification(xhr.responseJSON?.error || "Error retrieving user details", "error");
        }
    });
}


function updateUsername(oldUsername) {
    const newUsername = document.getElementById('editName').value.trim();
    if (newUsername && newUsername !== oldUsername) {
        $.ajax({
            url: '/users',
            type: 'PUT',
            headers: { "Content-Type": "application/json" },
            data: JSON.stringify({ oldUsername, newUsername }),
            success: function(response) {
                showNotification("Username updated successfully", "success");
                getRegisteredUsers(); // Refresh the user list
                bootstrap.Modal.getInstance(document.getElementById('userDetailsModal')).hide();
            },
            error: function(xhr, status, error) {
                console.error('Error updating username:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
                showNotification("Error updating username: " + errorMessage, "error");
            }
        });
    }
}

function deleteUser(username) {
    if (confirm(`Are you sure you want to delete user ${username}? This will also delete their photo.`)) {
        $.ajax({
            url: `/users/${username}`,
            type: 'DELETE',
            success: function(response) {
                showNotification("User deleted successfully", "success");
                getRegisteredUsers(); // Refresh the user list
                bootstrap.Modal.getInstance(document.getElementById('userDetailsModal')).hide();
            },
            error: function(xhr, status, error) {
                console.error('Error deleting user:', error);
                const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
                showNotification("Error deleting user: " + errorMessage, "error");
            }
        });
    }
}


function getInfo(){
    getApartmentInfo();
    getEmailInfo();
    getReservations();
    getUserInfo();
    getPdfFilename();
    getCommonAreas();
    getRegisteredUsers();
}
document.addEventListener('DOMContentLoaded', (event) => {
    
    var collapseElementList = [].slice.call(document.querySelectorAll('.collapse'))
    var collapseList = collapseElementList.map(function (collapseEl) {
        return new bootstrap.Collapse(collapseEl, {
            toggle: false
        })
    })

});
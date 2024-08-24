function sendApartment() {
    const apartmentNumber = document.getElementById("apartment-number").value.trim();
    const apartmentPhone = document.getElementById("apartment-phone").value.trim();

    if (!apartmentNumber || !apartmentPhone) {
        alert("Please fill in all fields.");
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
                li.className = 'list-group-item';
                li.innerHTML = `<strong>Apt ${apartmentNumber}:</strong> ${formatPhoneNumber(apartmentPhone)}`;
                listApartment.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting apartment info:', error);
            showNotification("Error retrieving apartment information", "error");
        }
    });
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
        alert("Please fill in both name and email fields.");
        return;
    }

    $.ajax({
        url: '/email',
        type: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        data: JSON.stringify({"email": email, "name": personName}),
        success: function(data) {
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
                li.innerHTML = `<strong>${name}</strong><br>${email}`;
                listEmails.appendChild(li);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error getting contact info:', error);
            showNotification("Error retrieving contact information", "error");
        }
    });
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
                document.getElementById('welcome-message').textContent = `Welcome to Naia, ${data.given_name}!`;
            }else{
                document.getElementById('welcome-message').textContent = `Welcome to Naia!`;
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







function getInfo(){
    getApartmentInfo();
    getEmailInfo();
    getReservations();
    getUserInfo();
}
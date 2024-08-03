
function sendApartment(){

    apartmentNumber = document.getElementById("apartment-number").value;
    apartmentPhone = document.getElementById("apartment-phone").value;

    if (!apartmentNumber || !apartmentPhone){
        alert("Please fill all the fields");
        return  
    }

    data = {"apartmentNumber": apartmentNumber, "apartmentPhone": apartmentPhone}
    $.ajax({
        url: '/apartment',
        type: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        data: JSON.stringify(data),
        success: function(data) {
            console.log('Apartment sent successfully');
            document.getElementById("apartment-number").value = "";
            document.getElementById("apartment-phone").value = "";
            alert("Apartment sent successfully");
            getApartmentInfo();
        },
        error: function(xhr, status, error) {
            console.error('Error sending apartment:', error);
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
            alert("Error sending apartment: " + errorMessage);
        }
    });
}




function getApartmentInfo(){
    $.ajax({
        url: '/apartment',
        type: 'GET',
        success: function(data) {
            listApartment = document.getElementById("listApartments");
            data = [data];    
            listApartment.innerHTML = "";
            data.forEach(apartment => {
                for (const [apartmentNumber, apartmentPhone] of Object.entries(apartment)) {
                    listApartment.innerHTML += `<li>Apartment number: ${apartmentNumber} - Phone: ${apartmentPhone}</li>`;
                }
            });        
        },
        error: function(xhr, status, error) {
            console.error('Error getting info:', error);
            alert("Error getting the email info ");
        }
    });
}


function sendEmailInfo(){
    email = document.getElementById("person-email").value;
    personName = document.getElementById("person-name").value;

    $.ajax({
        url: '/email',
        type: 'POST',
        headers: {
            "Content-Type": "application/json",
        },
        data: JSON.stringify({"email": email, "name": personName}),
        success: function(data) {
            console.log('Email sent successfully');
            document.getElementById("person-email").value = "";
            document.getElementById("person-name").value = "";
            alert("Email sent successfully");
            getEmailInfo();
        },
        error: function(xhr, status, error) {
            console.error('Error sending email:', error);
            const errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Unknown error";
            alert("Error sending email: " + errorMessage);
        }
    });

}

function getEmailInfo(){
    $.ajax({
        url: '/email',
        type: 'GET',
        success: function(data) {
            listEmails = document.getElementById("listPeopleEmail");
            data = [data];    
            listEmails.innerHTML = "";
            data.forEach(emailInfo => {
                for (const [name, email] of Object.entries(emailInfo)) {
                    listEmails.innerHTML += `<li>Email: ${email} - Name: ${name}</li>`;
                }
            });        
        },
        error: function(xhr, status, error) {
            console.error('Error getting info:', error);
            alert("Error getting the email info ");
        }
    });
}








function getInfo(){
    getApartmentInfo();
    getEmailInfo();
}
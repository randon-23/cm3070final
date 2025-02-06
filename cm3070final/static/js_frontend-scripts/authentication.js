function togglePasswordVisibility() {
    const passwordField = document.getElementById("id_password");
    const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
    passwordField.setAttribute("type", type);
}

// Initialize intl-tel-input for Phone Input
const phoneInputField = document.querySelector("#contact_number");
if (phoneInputField) {
    const iti = intlTelInput(phoneInputField, {
        initialCountry: "mt",  // Default country (Malta)
        utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17/build/js/utils.js",  // For advanced formatting
    });

    // Update the input value before form submission
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", function (e) {
            console.log(iti.getNumber());
            phoneInputField.value = iti.getNumber();  // Set full international number
        });
    }
}
function togglePasswordVisibility() {
    const passwordField = document.getElementById("id_password");
    const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
    passwordField.setAttribute("type", type);
}
function showLogoutMessage(event) {
    let response = event.detail.xhr.responseText;
    try {
        let data = JSON.parse(response);
        console.log(data);
        document.getElementById("logout-modal-content").innerHTML = `<p>${data.message}</p>`;

        let modal = document.getElementById("logout-modal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        setTimeout(() => {
            window.location.href = "/accounts/auth/?type=login";
        }, 2000);
    } catch (error) {
        console.error("Invalid JSON response:", response);
    }
}
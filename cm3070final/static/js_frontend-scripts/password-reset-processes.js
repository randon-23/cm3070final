
function showPasswordResetMessage(event) {
    console.log("Password reset message fired!", event);
    let response = event.detail.xhr.responseText;
    console.log(response);
    try{
        let data = JSON.parse(response);
        console.log(data)
        if(event.detail.xhr.status === 200){
            document.getElementById("password-reset-modal-content").innerHTML = `<p>${data.message}</p>`;
        } else{
            document.getElementById("password-reset-modal-content").innerHTML = `<p>${data.error}</p>`;
        }
        
        document.getElementById("password-reset-modal").classList.remove("hidden");
        document.getElementById("password-reset-modal").classList.add("flex");
        if (window.location.search.includes("reset_stage=confirm") && event.detail.xhr.status === 200){
            document.getElementById("confirm-image-container").innerHTML = `<img src="/static/images/authenticated.svg" alt="Done" class="w-32 mx-auto mb-4">`
            let countdownContainer = document.getElementById("countdown-container");
            if (countdownContainer) {
                document.getElementById("countdown-container").innerHTML = `<p class="mt-4 text-gray-600">
                    You will be redirected to the login page in <strong id="countdown">3</strong> seconds.
                </p>`;
                
                let timeLeft = 3;
                const redirectUrl = '/accounts/auth/?type=login'
                const countdownElement = document.getElementById("countdown");
                const countdown = setInterval(() => {
                    timeLeft--
                    countdownElement.textContent = timeLeft;

                    if (timeLeft <= 0){
                        clearInterval(countdown)
                        window.location.href = redirectUrl;
                    }
                }, 1000)   
            }
        } else if(event.detail.xhr.status !== 200){
            document.getElementById("confirm-image-container").innerHTML = `<img src="/static/images/something-went-wrong.svg" alt="Error" class="w-32 mx-auto mb-4">`
        }
    }
    catch (error) {
        console.error("Invalid JSON response:", response);
    }
}

document.addEventListener("htmx:afterRequest", function(event) {
    showPasswordResetMessage(event);
});

function hideModal() {
    document.getElementById("password-reset-modal").classList.add("hidden");
    document.getElementById("password-reset-modal").classList.remove("flex");
}
// Close modal when clicking outside it
document.addEventListener("click", function (event) {
    const modalContainer = document.querySelector("#modal-container");
    if (modalContainer && event.target === modalContainer) {
        hideModal();
    }
  });
  
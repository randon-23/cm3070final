document.addEventListener("htmx:afterSwap", function (event) {
  // Check if the modal was loaded
  if (event.detail.target.id === "modal-container") {
      const modal = document.querySelector("#modal-container .modal");
      const redirectUrl = modal.dataset.redirectUrl;
      const countdownElement = document.getElementById("countdown");

      if (modal) {
          modal.classList.add("modal-open");
      }

      let timeLeft = 3;
      const countdown = setInterval(() => {
          timeLeft--
          countdownElement.textContent = timeLeft;

          if (timeLeft <= 0){
              clearInterval(countdown)
              window.location.href = redirectUrl;
          }
      }, 1000)
  }
});

// Close modal when clicking outside it
document.addEventListener("click", function (event) {
  const modalContainer = document.querySelector("#modal-container");
  if (modalContainer && event.target === modalContainer) {
      modalContainer.innerHTML = ""; 
  }
});

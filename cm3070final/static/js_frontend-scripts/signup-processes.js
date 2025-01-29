document.addEventListener("htmx:afterSwap", function (event) {
  // Check if the modal was loaded
  if (event.detail.target.id === "modal-container") {
      const modal = document.querySelector("#modal-container .modal");

      if (modal) {
          modal.classList.add("modal-open");
            
          const redirectUrl = modal.dataset.redirectUrl;

          if (redirectUrl) {
              setTimeout(() => {
                  window.location.href = redirectUrl; 
              }, 3000);
          }
      }
  }
});

// Close modal when clicking outside it
document.addEventListener("click", function (event) {
  const modalContainer = document.querySelector("#modal-container");
  if (modalContainer && event.target === modalContainer) {
      modalContainer.innerHTML = ""; 
  }
});

document.addEventListener("DOMContentLoaded", function () {
    let selectedRecipient = null;

    // Open message modal and set recipient ID
    document.querySelectorAll(".open-message-modal").forEach(button => {
        button.addEventListener("click", function () {
            selectedRecipient = this.getAttribute("data-recipient-id");
            document.getElementById("send-message-modal").classList.remove("hidden");
            document.getElementById("send-message-modal").classList.add("flex");
        });
    });

    // Close message modal
    document.querySelector(".close-message-modal").addEventListener("click", function () {
        document.getElementById("send-message-modal").classList.add("hidden");
        document.getElementById("send-message-modal").classList.remove("flex");
    });
});
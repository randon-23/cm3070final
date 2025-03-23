function markAsRead(notificationId) {
    const el = document.getElementById(`notification-${notificationId}`);
    if (el) {
        el.classList.add('transition', 'opacity-0');
        setTimeout(() => el.remove(), 300);
    }
}

document.addEventListener("htmx:afterRequest", function () {
    console.log("htmx:afterRequest event triggered!");
    const remainingNotifications = document.querySelectorAll('#notifications-container > div[id^="notification-"]');
    console.log(remainingNotifications);
    if (remainingNotifications.length <= 1) {
        const blip = document.getElementById('notification-blip');
        if (blip) {
            blip.classList.add('hidden');
        }

        const container = document.getElementById("notifications-container");
        if (container) {
            container.innerHTML = `<p class="text-gray-600 text-center">No new notifications.</p>`;
        }
    }
});
const notificationSocket = new WebSocket('ws://'+window.location.host+'/ws/notifications/');

notificationSocket.onopen = function (event) {
    console.log('Notification WebSocket connected.');
};

notificationSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log('New Notification:', data);

    // Show the notification popup
    showNotificationPopup(data.title, data.message);

    // Show the red notification blip on the sidebar button
    const notificationIndicator = document.getElementById('notification-blip');
    if (notificationIndicator) {
        notificationIndicator.classList.remove('hidden');
    }
};

notificationSocket.onclose = function (event) {
    console.log('Notification WebSocket closed.');
}

notificationSocket.onerror = function (event) {
    console.error('Notification WebSocket error:', event);
}

// Function to show a notification popup
function showNotificationPopup(title, message) {
    // Create notification div
    const notificationContainer = document.createElement('div');
    notificationContainer.className = "notification-popup bg-blue-500 text-white p-4 rounded-lg shadow-lg transition-opacity duration-1000 opacity-100";
    notificationContainer.style.position = "fixed";
    notificationContainer.style.top = "20px";
    notificationContainer.style.right = "20px";
    notificationContainer.style.zIndex = "9999";

    notificationContainer.innerHTML = `
        <strong>${title}</strong>
        <p>${message}</p>
    `;

    document.body.appendChild(notificationContainer);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notificationContainer.style.opacity = "0";
        setTimeout(() => notificationContainer.remove(), 1000);
    }, 5000);
}

function hideNotificationBlip() {
    const notificationIndicator = document.getElementById('notification-blip');
    if (notificationIndicator) {
        notificationIndicator.classList.add('hidden');
    }
}
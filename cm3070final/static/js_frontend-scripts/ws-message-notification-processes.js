const messageNotificationSocket = new WebSocket('ws://'+window.location.host+'/ws/message_notifications/');

messageNotificationSocket.onopen = function (event) {
    console.log('Message Notification WebSocket connected.');
}

messageNotificationSocket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log('New Notification:', data);
    let pathname = window.location.pathname;

    // Show the notification for mesages popup if the user is not in the chat page
    if(!pathname.startsWith('/chats')){
        showMessageNotificationPopup(data.title, data.message);

        const messageNotificationIndicator = document.getElementById('message-notification-blip');
        if (messageNotificationIndicator) {
            messageNotificationIndicator.classList.remove('hidden');
        }
    }
}

messageNotificationSocket.onclose = function (event) {
    console.log('Message Notification WebSocket closed.');
}

messageNotificationSocket.onerror = function (event) {
    console.error('Message Notification WebSocket error:', event);
}

function showMessageNotificationPopup(title, message) {
    const notificationContainer = document.createElement('div');
    notificationContainer.className = "notification-popup bg-blue-500 text-white p-4 rounded-lg shadow-lg transition-opacity duration-1000 opacity-100";
    notificationContainer.style.position = "fixed";
    notificationContainer.style.bottom = "20px";
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
    }, 3000);
}
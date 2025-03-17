function markAsRead(notificationId) {
    let notificationElement = document.getElementById(`notification-${notificationId}`);
    if (notificationElement) {
        notificationElement.remove();
        window.location.reload();
    }
}
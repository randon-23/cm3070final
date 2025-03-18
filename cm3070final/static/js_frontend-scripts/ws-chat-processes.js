const chatSockets = {};  // Stores WebSocket connections
let activeChatId = null;  // Tracks which chat is open

window.onload = function () {
    const chatList = document.querySelectorAll("#chat-list li");
    chatList.forEach(chatItem => {
        const chatId = chatItem.id.replace("chat-", "");
        connectToChat(chatId);
    });
};

window.addEventListener("beforeunload", function () {
    Object.values(chatSockets).forEach(socket => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    });
});

// Connect to WebSocket for a specific chat
function connectToChat(chatId) {
    if (chatSockets[chatId]) return;  // Avoid duplicate connections

    const socket = new WebSocket(`ws://${window.location.host}/ws/chat/${chatId}/`);
    chatSockets[chatId] = socket;

    socket.onopen = function () {
        console.log(`Connected to chat ${chatId}`);
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("New Message:", data);

        // Append message to the chat's message container
        displayMessage(chatId, data);

        // If the chat is not active, show the "New Message" alert
        if (activeChatId !== chatId) {
            document.getElementById(`new-message-${chatId}`).classList.remove("hidden");
        }
    };

    socket.onclose = function () {
        console.log(`Disconnected from chat ${chatId}`);
        delete chatSockets[chatId];
    };

    socket.onerror = function (error) {
        console.error("Chat WebSocket error:", error);
    };
}

// Switch active chat
function selectChat(chatId, chatTitle) {
    activeChatId = chatId;

    // Update chat header with selected chat participant's name
    document.getElementById("chat-title").textContent = chatTitle;

    // Hide default message and show messages
    document.getElementById("default-message").classList.add("hidden");
    document.querySelectorAll(".chat-messages").forEach(el => el.classList.add("hidden"));
    document.getElementById(`messages-${chatId}`).classList.remove("hidden");

    // Show chat input field
    document.getElementById("chat-input-container").classList.remove("hidden");

    // Hide "New Message" alert
    document.getElementById(`new-message-${chatId}`)?.classList.add("hidden");
}

// Display incoming message in chat window
function displayMessage(chatId, data) {
    const messageElement = document.createElement("div");
    messageElement.className = `p-2 rounded my-1 ${data.sender === activeChatId ? "bg-blue-500 text-white text-right" : "bg-gray-200 text-left"}`;
    messageElement.innerHTML = `<strong>${data.sender}:</strong> ${data.message}`;
    
    document.getElementById(`messages-${chatId}`).appendChild(messageElement);
}

// Send a message
function sendMessage() {
    const messageInput = document.getElementById("message-input");
    if (!messageInput.value.trim()) return;

    const chatId = activeChatId;
    chatSockets[chatId].send(JSON.stringify({
        message: messageInput.value
    }));

    messageInput.value = "";
}

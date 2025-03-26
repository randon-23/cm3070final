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
function selectChat(chatId, chatTitle, profileImgUrl) {
    activeChatId = chatId;

    // Update chat header with selected chat participant's name
    document.getElementById("chat-title").textContent = chatTitle;

    // Hide default message and show messages
    document.getElementById("default-message").classList.add("hidden");
    document.querySelectorAll(".chat-messages").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".chat-messages").forEach(el => el.classList.remove("flex"));
    document.getElementById(`messages-${chatId}`).classList.remove("hidden");
    document.getElementById(`messages-${chatId}`).classList.add("flex");

    // Show chat input field
    document.getElementById("chat-input-container").classList.remove("hidden");

    // Hide "New Message" alert
    document.getElementById(`new-message-${chatId}`)?.classList.add("hidden");

    // Show profile image on title bar    
    document.getElementById("chat-title-img").src = profileImgUrl;
    document.getElementById("chat-title-img").classList.remove("hidden");

    const msgContainer = document.getElementById('chat-messages');
    setTimeout(() => {
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }, 50);
}

// Display incoming message in chat window
function displayMessage(chatId, data) {
    const messageWrapper = document.createElement("div");

    const isCurrentUser = data.sender === CURRENT_USER_UUID;
    messageWrapper.className = `flex mx-2 my-2 ${isCurrentUser ? "justify-end" : "justify-start"}`;

    const profileImg = document.createElement("img");
    profileImg.src = data.sender_profile_img || (data.is_volunteer
        ? "/static/images/default_volunteer.svg"
        : "/static/images/default_organization.svg");
    profileImg.alt = "Profile";
    profileImg.className = "w-8 h-8 rounded-full object-cover " + (isCurrentUser ? "ml-2" : "mr-2");

    const bubble = document.createElement("div");
    bubble.className = (isCurrentUser
        ? "bg-blue-500 text-white"
        : "bg-gray-200 text-gray-900") + " px-4 py-2 rounded-lg max-w-[70%] break-words relative";

    const messageContent = document.createElement("p");
    messageContent.textContent = data.message;

    const timestamp = document.createElement("p");
    const date = new Date(data.timestamp);
    const formattedTime = date.toLocaleString("en-GB", {
        month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit"
    });
    timestamp.textContent = formattedTime;
    timestamp.className = (isCurrentUser ? "text-xs mt-1 opacity-70 text-right" : "text-xs mt-1 opacity-70 text-left");

    bubble.appendChild(messageContent);
    bubble.appendChild(timestamp);

    if (!isCurrentUser) {
        messageWrapper.appendChild(profileImg);
        messageWrapper.appendChild(bubble);
    } else {
        messageWrapper.appendChild(bubble);
        messageWrapper.appendChild(profileImg);
    }

    const container = document.getElementById(`messages-${chatId}`);
    container.appendChild(messageWrapper);
    const parentContainer = document.getElementById('chat-messages')
    setTimeout(() => {
        parentContainer.scrollTop = parentContainer.scrollHeight;
    }, 50);
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

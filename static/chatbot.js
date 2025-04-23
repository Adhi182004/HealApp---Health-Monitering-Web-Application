document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const message = input.value.trim();
        if (message === "") return;

        appendMessage("You", message, "user-msg");
        input.value = "";

        fetch("/chatbot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.reply) {
                appendMessage("Bot", data.reply, "bot-msg");
            } else {
                appendMessage("Bot", "Sorry, I didn't understand that.", "bot-msg");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("Bot", "Something went wrong.", "bot-msg");
        });
    });

    function appendMessage(sender, text, className) {
        const messageDiv = document.createElement("div");
        messageDiv.className = className;
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
